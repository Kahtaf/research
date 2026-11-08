#!/usr/bin/env python3
"""VM-only graph qualification: never import capture, gates, ELF or packages."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if sys.platform != 'linux' or ROOT != Path('/srv/android/asus-official-runtime-capture/preparation-v4'):
    raise SystemExit('exact owned VM preparation required')
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (900, 900))
resource.setrlimit(resource.RLIMIT_FSIZE, (8*1024**3, 8*1024**3))
sys.path.insert(0, str(ROOT/'source'))
from safeio import Tree, need, permitted, Refusal, fingerprint, write_json
from graph import Graph

start = time.monotonic()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
fixture = ROOT/'graph-qualification-002'
fixture.mkdir(mode=0o700)  # exclusive; failures are never reused/deleted
limits = json.loads((ROOT/'inputs/profile-r8.json').read_bytes())['limits']
paths = ['out/build-lineage_p00a.ninja', 'out/soong/build.lineage_p00a.ninja', 'out/combined-lineage_p00a.ninja']
receipt = {'schema': 1, 'scope': 'isolated-graph-parser-index-provenance-paths-only',
           'actual_select_verify_copy': False, 'build_success_accepted': False,
           'payload_elf_policy_apex_image_contents_opened': False,
           'started_utc': started, 'limits': limits,
           'cpu_seconds_limit': 900, 'wall_seconds_limit': 1200,
           'fixture_storage_budget_bytes': 16*1024**3,
           'cpu_affinity': sorted(os.sched_getaffinity(0)),
           'address_space_limit_bytes': resource.getrlimit(resource.RLIMIT_AS)[0],
           'tested_module_sha256': {n: hashlib.sha256((ROOT/'source'/n).read_bytes()).hexdigest() for n in ('graph.py','safeio.py')},
           'source_before': {}, 'source_after': {}, 'frozen': {}, 'status': 'FAILED'}
graph = None
source = None
frozen = None
try:
    space = os.statvfs(fixture)
    receipt['available_storage_before_bytes'] = space.f_bavail * space.f_frsize
    need(receipt['available_storage_before_bytes'] >= 10*1024**3, 'STORAGE', '8 GiB index plus 2 GiB free reserve required')
    frozen = Tree(ROOT/'graph-fixture/frozen')
    geometry = json.loads((ROOT/'graph-fixture/block-geometry.json').read_bytes())
    for row in geometry['graphs']:
        need(row['pin'] == frozen.digest(row['path'], limits['graph_file_bytes']), 'DRIFT', row['path'])
    receipt['frozen_geometry_receipt_sha256'] = hashlib.sha256((ROOT/'graph-fixture/block-geometry.json').read_bytes()).hexdigest()
    index_start = time.monotonic()
    graph = Graph(frozen, paths, fixture/'graph-index.sqlite', limits)
    receipt['index_elapsed_seconds'] = round(time.monotonic()-index_start, 3)
    receipt['graphs'] = graph.stats
    receipt['frozen'] = graph.pins
    receipt['row_counts'] = graph.counts
    receipt['max_line_bytes'] = graph.max_line_bytes
    receipt['max_block_bytes'] = graph.max_block_bytes
    receipt['index_bytes'] = (fixture/'graph-index.sqlite').stat().st_size
    receipt['sqlite_page_size'] = graph.db.execute('PRAGMA page_size').fetchone()[0]
    receipt['sqlite_page_count'] = graph.db.execute('PRAGMA page_count').fetchone()[0]
    receipt['sqlite_integrity_check'] = graph.db.execute('PRAGMA quick_check').fetchone()[0]
    need(receipt['sqlite_integrity_check'] == 'ok', 'INDEX_INTEGRITY', 'quick_check')
    selector = json.loads((ROOT/'inputs/selector.json').read_bytes())
    targets = ['out/target/product/p00a/'+p for p in selector['required']]
    targets += list(selector['generation_outputs'].values())
    resolutions = []
    for target in dict.fromkeys(targets):
        try:
            edge = graph.edge(target)
            explicit = [d['path'] for d in edge['dependencies'] if d['kind']=='explicit']
            resolutions.append({'target': target, 'rule': edge['rule'],
                                'explicit_inputs': explicit,
                                'graph': graph.records['edge:'+target]['graph'],
                                'line': graph.records['edge:'+target]['line'],
                                'raw_sha256': hashlib.sha256(edge['raw'].encode()).hexdigest(),
                                'expanded_rule_sha256': hashlib.sha256((edge['expanded_rule'] or '').encode()).hexdigest(),
                                'dependency_count': len(edge['dependencies'])})
        except (Refusal, ValueError) as error:
            resolutions.append({'target': target, 'error': str(error)})
    receipt['selector_producer_resolutions'] = resolutions
    # Resolve metadata/package graph closure only. Dependency path strings are data;
    # excluded private/image paths are counted, never opened or hashed.
    queue = [(t, 0) for t in dict.fromkeys(targets)]
    seen = set()
    excluded = 0
    unresolved = []
    while queue:
        path, depth = queue.pop(0)
        if path in seen:
            continue
        need(depth < 30 and len(seen) < limits['edges'], 'GRAPH_DEPTH', path)
        seen.add(path)
        try:
            edge = graph.edge(path)
        except (Refusal, ValueError) as error:
            unresolved.append({'path': path, 'error': str(error)})
            continue
        follow = any(token in path for token in ('/selinux/','/sepolicy/','/vintf/','/linkerconfig/','build.prop','apexkeys.txt','api_fingerprint','product_config')) or path.endswith(('.apex','.capex','.apex.unsigned'))
        for dep in edge['dependencies']:
            if dep['kind'] in ('order_only','validation'):
                continue
            name = dep['path']
            try:
                permitted(name)
            except Refusal:
                excluded += 1
                continue
            if (follow or dep['kind']=='explicit') and graph.has_edge(name):
                queue.append((name,depth+1))
    receipt['graph_only_provenance'] = {'resolved_edge_count': len(seen), 'excluded_dependency_path_count': excluded,
                                        'unresolved': unresolved, 'recorded_evidence_bytes': graph.evidence_bytes,
                                        'payload_hash_or_equality_validation': False}
    graph.recheck()
    receipt['status'] = 'PASS' if not any('error' in r for r in resolutions) and not unresolved else 'GRAPH_RESOLUTION_BLOCKER'
except BaseException as error:
    receipt['error'] = type(error).__name__+': '+str(error)
finally:
    if graph is not None:
        graph.close()
    if frozen is not None:
        frozen.close()
    if source is not None:
        source.close()
    receipt['elapsed_seconds'] = round(time.monotonic()-start, 3)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    receipt['cpu_seconds'] = round(usage.ru_utime+usage.ru_stime, 3)
    receipt['max_rss_KiB'] = usage.ru_maxrss
    receipt['fixture_storage_bytes'] = sum(p.stat().st_size for folder in ('graph-fixture','graph-qualification-002') for p in (ROOT/folder).rglob('*') if p.is_file())
    receipt['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    need(receipt['fixture_storage_bytes'] <= receipt['fixture_storage_budget_bytes'], 'STORAGE', 'owned fixture storage ceiling')
    write_json(fixture/'qualification.json', receipt)
    print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt['status']=='PASS' else 1)
