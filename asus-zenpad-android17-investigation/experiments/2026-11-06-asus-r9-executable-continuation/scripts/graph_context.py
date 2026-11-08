"""Bounded selected-module/rule observations; no Ninja/Siso invocation."""
import bisect
import hashlib
import re
from pathlib import Path

HEADER = re.compile(rb'^# Module:  ([^\n]+)\n', re.M)
MAX_MODULE = 6 * 1024 * 1024


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def module_identity(target):
    parts = target.split('/')
    if not target.startswith('out/soong/.intermediates/'):
        return None
    index = next(i for i, value in enumerate(parts) if value.startswith(('android_', 'linux_')))
    return {'module': parts[index - 1], 'variant': parts[index],
            'module_path': '/'.join(parts[3:index - 1])}


def module_block(aosp, name, hint=None):
    aosp = Path(aosp)
    if hint:
        path = aosp / hint['path']
        with path.open('rb') as stream:
            stream.seek(hint['offset']); data = stream.read(hint['bytes'])
        if data.startswith(('# Module:  ' + name + '\n').encode()) and (
                'sha256' not in hint or hash_bytes(data) == hint['sha256']):
            return dict(path=hint['path'], offset=hint['offset'], bytes=len(data),
                        sha256=hash_bytes(data), text=data.decode())
    shards = []
    for number in range(10):
        path = aosp / f'out/soong/build.lineage_p00a.{number}.ninja'
        if not path.is_file():raise ValueError('Missing actual selected graph shard: '+str(path))
        with path.open('rb') as stream:
            first = HEADER.search(stream.read(1024 * 1024))
        if first is None:
            raise ValueError('No module header at shard start')
        shards.append((first[1].decode(), number))
    # Shard zero has a special generated overlay prefix before ordinary modules.
    shards[0] = ('', 0)
    if [x[0] for x in shards] != sorted(x[0] for x in shards):
        raise ValueError('Module shard order changed')
    candidates = [number for index, (first, number) in enumerate(shards)
                  if first <= name and (index == 9 or name <= shards[index + 1][0])]
    for number in candidates:
        rel = f'out/soong/build.lineage_p00a.{number}.ninja'; path = aosp / rel
        size = path.stat().st_size; lo, hi = 0, size
        with path.open('rb') as stream:
            for _ in range(22):
                if hi - lo < 4 * 1024 * 1024:
                    break
                mid = (lo + hi) // 2; stream.seek(mid)
                data = stream.read(min(4 * 1024 * 1024, size - mid))
                found = HEADER.search(data)
                if found is None:
                    # A preceding unrelated generated module can exceed 4 MiB.
                    # Widen this single seek window, never stream/reindex graphs.
                    stream.seek(mid);data=stream.read(min(64*1024*1024,size-mid))
                    found=HEADER.search(data)
                if found is None:
                    raise ValueError('No header in bounded module search: '+name+' at '+str(mid))
                # Blueprint sorts namespace-qualified numeric names before root names.
                # Shard zero begins with those separate namespace modules.
                end = HEADER.search(data, found.end())
                section = data[found.start():end.start() if end else len(data)]
                namespaced = re.search(rb'^m\.[0-9]+-', section, re.M) is not None
                if namespaced or found[1].decode() < name:
                    lo = mid + found.start()
                else:
                    hi = mid
            base = max(0, lo - 1024); stream.seek(base)
            data = stream.read(min(12 * 1024 * 1024, size - base))
        hits = list(HEADER.finditer(data))
        starts = [i for i, match in enumerate(hits) if match[1].decode() == name]
        if not starts:
            continue
        start = hits[starts[0]].start(); end = None
        for match in hits[starts[0] + 1:]:
            if match[1].decode() != name:
                end = match.start(); break
        if end is None or end - start > MAX_MODULE:
            raise ValueError('Selected module exceeds bounded window: ' + name)
        block = data[start:end]
        return dict(path=rel, offset=base + start, bytes=len(block),
                    sha256=hash_bytes(block), text=block.decode())
    raise ValueError('Selected module missing: ' + name)


def logical_lines(text):
    pending = []
    for line in text.splitlines(keepends=True):
        if line.endswith('$\n'):
            pending.append(line[:-2]); continue
        if pending:
            pending.append(line); line = ''.join(pending); pending = []
        yield line
    if pending:
        raise ValueError('Unterminated selected Ninja continuation')


def parse(text):
    edges, rules, variables = {}, {}, {}
    current = None; context = None
    for line in logical_lines(text):
        if line.startswith('build '):
            head, sep, tail = line[6:].partition(': ')
            if not sep:
                raise ValueError('Malformed selected build edge')
            tokens = tail.split()
            if not tokens:
                raise ValueError('Missing selected rule')
            outputs = [x for x in head.split() if x != '|']
            inputs, explicit, order_only = [], [], []
            mode = 'explicit'
            for value in tokens[1:]:
                if value == '|': mode = 'implicit'; continue
                if value == '||': mode = 'order'; continue
                (order_only if mode == 'order' else inputs).append(value)
                if mode == 'explicit': explicit.append(value)
            current = {'rule': tokens[0], 'outputs': outputs, 'inputs': inputs,
                       'explicit_inputs': explicit, 'order_only': order_only,
                       'variables': {}, 'text': line}
            for output in outputs:
                if output in edges:
                    raise ValueError('Duplicate selected graph target: ' + output)
                edges[output] = current
            context = 'edge'
        elif line.startswith('rule '):
            name = line.split()[1]; current = {'variables': {}, 'text': line}
            rules[name] = current; context = 'rule'
        elif line[:1].isspace() and current is not None:
            current['text'] += line
            key, sep, value = line.strip().partition(' = ')
            if sep:
                current['variables'][key] = value
        else:
            current = None; context = None
            key, sep, value = line.rstrip('\n').partition(' = ')
            if sep and not key.startswith('#'):
                variables[key] = value
    return edges, rules, variables


def variant_text(block, module, variant):
    parts = re.split(r'(?=^# Module:  )', block, flags=re.M)
    matches = [part for part in parts if part.startswith('# Module:  ' + module + '\n')
               and re.search(r'^# Variant: ' + re.escape(variant) + r'$', part, re.M)]
    if len(matches) != 1:
        raise ValueError('Wrong/missing selected module variant')
    return matches[0]


def physical_prefixes(path, cap=1024 * 1024):
    """Emit bounded line prefixes, discarding oversized unrelated command bodies."""
    offset = start = 0; chunks = []; kept = 0; truncated = False
    with Path(path).open('rb') as stream:
        while data := stream.read(65536):
            pos = 0
            while pos < len(data):
                end = data.find(b'\n', pos)
                stop = len(data) if end < 0 else end + 1
                piece = data[pos:stop]
                if kept < cap:
                    take = min(cap - kept, len(piece)); chunks.append(piece[:take]); kept += take
                    truncated |= take != len(piece)
                else:
                    truncated = True
                offset += len(piece); pos = stop
                if end >= 0:
                    yield start, b''.join(chunks), truncated, offset
                    start = offset; chunks = []; kept = 0; truncated = False
        if kept or truncated:
            yield start, b''.join(chunks), truncated, offset


def kati_edges(aosp, targets):
    path = Path(aosp) / 'out/build-lineage_p00a.ninja'
    edges, rule_offsets = {}, {}
    current = None
    for offset, raw, truncated, end in physical_prefixes(path):
        if raw.startswith(b'rule '):
            rule_offsets[raw.split()[1].decode()] = offset
        if current is not None:
            if raw[:1] in (b' ', b'\t'):
                if truncated:
                    raise ValueError('Oversized selected Kati edge')
                current['raw'] += raw; current['end'] = end; continue
            edges[current['target']] = current; current = None
        if not raw.startswith(b'build '):
            continue
        head, sep, _ = raw[6:].partition(b': ')
        hits = set(head.decode().split()) & targets
        if not hits:
            continue
        if truncated or not sep or len(hits) != 1:
            raise ValueError('Unsupported selected Kati build header')
        current = dict(target=hits.pop(), offset=offset, end=end, raw=raw)
    if current is not None:
        edges[current['target']] = current
    result = {}
    with path.open('rb') as stream:
        for target, row in edges.items():
            parsed = parse(row['raw'].decode())[0][target]
            rule = parsed['rule']; begin = rule_offsets[rule]
            stream.seek(begin); lines = [stream.readline(65536)]
            for _ in range(100):
                line = stream.readline(65536)
                if not line[:1].isspace(): break
                if len(line) == 65536 and not line.endswith(b'\n'):
                    raise ValueError('Oversized selected Kati rule')
                lines.append(line)
            rule_raw = b''.join(lines)
            result[target] = dict(path=str(path.relative_to(aosp)), offset=row['offset'],
                                  bytes=len(row['raw']), sha256=hash_bytes(row['raw']),
                                  text=row['raw'].decode(), rule_offset=begin,
                                  rule_bytes=len(rule_raw), rule_sha256=hash_bytes(rule_raw),
                                  rule_text=rule_raw.decode())
    if set(result) != targets:
        raise ValueError('Missing selected installed Kati edges: ' + str(sorted(targets - result.keys())))
    return result


def read_range(aosp, row, rule=False):
    with (Path(aosp) / row['path']).open('rb') as stream:
        stream.seek(row['rule_offset'] if rule else row['offset'])
        return stream.read(row['rule_bytes'] if rule else row['bytes']).decode()


def validate_context(aosp, record, catalog, cache):
    ref = record['graph_context']
    if ref['kind'] == 'SOONG_MODULE':
        name = ref['module']; row = catalog['modules'][name]
        if name not in cache:
            current = module_block(aosp, name, row)
            if current['sha256'] != row['sha256']:
                raise ValueError('Current graph module changed: ' + name)
            cache[name] = current
        text = variant_text(cache[name]['text'], name, ref['variant'])
        if hash_bytes(text.encode()) != ref['variant_sha256']:
            raise ValueError('Current graph variant/flags changed')
        edge = parse(text)[0].get(record['output'])
        if edge is None or hash_bytes(edge['text'].encode()) != ref['edge_sha256']:
            raise ValueError('Current selected graph predecessor changed')
        return edge
    row = catalog['kati'][record['output']]
    text, rule = read_range(aosp, row), read_range(aosp, row, True)
    if hash_bytes(text.encode()) != row['sha256'] or hash_bytes(rule.encode()) != row['rule_sha256']:
        raise ValueError('Current installed graph predecessor/rule changed')
    return parse(text)[0][record['output']]


def selected_graph(aosp, catalog, records):
    """Read the pinned selected module variants and installed predecessors only."""
    edges, rules, pins = {}, {}, {}
    variants = {}
    for row in records.values():
        ref = row['graph_context']
        if ref['kind'] == 'SOONG_MODULE':
            variants.setdefault(ref['module'], set()).add(ref['variant'])
    for name, wanted in variants.items():
        prepared = catalog['modules'][name]
        observed = module_block(aosp, name, prepared)
        if observed['sha256'] != prepared['sha256']:
            raise ValueError('Current selected graph module changed: ' + name)
        pins[name] = observed['sha256']
        for variant in wanted:
            part = variant_text(observed['text'], name, variant)
            selected, _, _ = parse(part)
            for target, edge in selected.items():
                if target in edges:
                    raise ValueError('Duplicate selected graph output: ' + target)
                edges[target] = edge
    for target, row in catalog['kati'].items():
        text, rule = read_range(aosp, row), read_range(aosp, row, True)
        if hash_bytes(text.encode()) != row['sha256'] or hash_bytes(rule.encode()) != row['rule_sha256']:
            raise ValueError('Current selected installed graph changed: ' + target)
        edges.update(parse(text)[0]); rules.update(parse(rule)[1])
        pins[target] = row['sha256']
    prefix = catalog['global_prefix']
    with (Path(aosp) / prefix['path']).open('rb') as stream:
        data = stream.read(prefix['bytes'])
    if hash_bytes(data) != prefix['sha256']:
        raise ValueError('Current selected global compiler/rule flags changed')
    rules.update(parse(data.decode())[1])
    names = {edge['rule'] for edge in edges.values()} - {'phony'}
    if not names <= rules.keys():
        raise ValueError('Missing selected compiler/linker rules: ' + str(sorted(names-rules.keys())))
    return edges, {'scope': 'EXPLICIT_SELECTED_MODULE_VARIANTS_AND_INSTALLED_PREDECESSORS',
                   'selected_graph_sha256': pins,
                   'global_prefix_sha256': prefix['sha256'],
                   'edges': edges, 'rules': {name: rules[name]['text'] for name in names}}
