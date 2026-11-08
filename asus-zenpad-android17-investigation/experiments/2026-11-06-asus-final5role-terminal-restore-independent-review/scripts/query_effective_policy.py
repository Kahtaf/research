"""Serial, bounded, existing native libsepol query; never writes a policy."""
from pathlib import Path
import hashlib
import json
import resource
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parents[1]
TOOL = ROOT / '2026-11-06-asus-recovery-diagnostic/artifacts/policy-query-n'
POLICY = ROOT / '2026-11-06-asus-stock-only-ram-rescue-build/artifacts/restore-sepolicy'
PHASE = ROOT / '2026-11-06-asus-recovery-phase-proof/context/restore-sepolicy'
EXPECTED = '16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(POLICY) == sha(PHASE) == EXPECTED

def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

actors = ['init', 'ueventd', 'adbd', 'shell', 'os_rescue', 'p10_restore']
nodes = ['rescue_recovery_device', 'rescue_disk_device', 'block_device',
         'rescue_boot_device', 'rescue_system_device', 'rescue_userdata_device']
execs = ['p10_restore_exec', 'os_rescue_exec', 'shell_exec', 'rootfs']
rows = []
started = time.monotonic()

def query(src, tgt, cls, process=False, transition=False):
    assert time.monotonic() - started < 60
    sc = f'u:r:{src}:s0'
    tc = f'u:{"r" if process else "object_r"}:{tgt}:s0'
    args = [str(TOOL), str(POLICY), sc, tc, cls]
    if transition:
        args.append('--transition')
    p = subprocess.run(args, capture_output=True, text=True, timeout=10, preexec_fn=limits)
    assert p.returncode == 0, (args, p.stderr)
    assert resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss < 1024**3
    row = dict(source=sc, target=tc, cls=cls, transition=transition,
               returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    if not transition:
        row['allowed'] = sorted(filter(None, p.stdout.split('allowed=')[1].split(' ')[0].strip().split(',')))
    rows.append(row)

for actor in actors:
    for j, node in enumerate(nodes):
        query(actor, node, 'blk_file')
        query(actor, actors[j], 'process', True)
        query(actor, actors[j], 'fd', True)
    for exe in execs:
        query(actor, exe, 'file')
    query(actor, 'kernel', 'security', True)
    query(actor, actor, 'capability', True)
assert len(rows) == 144
result = dict(policy_sha256=sha(POLICY), phase_copy_sha256=sha(PHASE), tool=str(TOOL.relative_to(ROOT)),
              tool_sha256=sha(TOOL), tool_source='2026-11-06-asus-recovery-diagnostic/source/policy_query.c',
              tool_source_sha256=sha(ROOT/'2026-11-06-asus-recovery-diagnostic/source/policy_query.c'),
              tool_source_build_equivalence_not_claimed=True,
              unsupported_transition_probe='Existing native executable returned 2 for --transition; no transition query pass claimed',
              limits=dict(serial=True, single_threaded_query=True, cpu_seconds_per_query=10,
                          wall_timeout_per_query=10, overall_seconds=60,
                          maxrss_acceptance_bytes=1024**3,
                          darwin_memory_setrlimit_rejected=True,
                          memory_bound='Actual child high-water RSS checked after every serial query; not a kernel memory quota',
                          hard_linux_cgroup_or_affinity_claim=False),
              child_maxrss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
              elapsed_seconds=time.monotonic()-started, rows=rows)
(OWN/'evidence/effective-policy.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(dict(policy_sha256=EXPECTED, rows=len(rows),
                     child_maxrss_bytes=result['child_maxrss_bytes'])))
for r in rows:
    if r['cls']=='blk_file' and ('userdata' in r['target'] or 'os_rescue:' in r['source'] or 'p10_restore:' in r['source']):
        print(r['source'], r['target'], ','.join(r['allowed']) or 'NONE')
