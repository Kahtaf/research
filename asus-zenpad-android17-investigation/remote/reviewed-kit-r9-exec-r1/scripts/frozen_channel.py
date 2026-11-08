"""Exact completed commands, native metrics and untouched Ninja corroboration."""
import base64
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shlex
from native_state import sha


def read(path):
    return json.loads(Path(path).read_text())


def produces(command, target):
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if len(words) >= 3 and words[0] in ('/bin/bash', '/bin/sh', 'bash', 'sh') and words[1] == '-c':
        words = shlex.split(words[2])
    if any(value == '-o' and words[index + 1] == target
           for index, value in enumerate(words[:-1])):
        return True
    for index, value in enumerate(words):
        if Path(value).name in ('llvm-ar', 'ar'):
            # ar's first non-option operand after its operation is the output archive.
            rest = words[index + 2:]
            if rest and rest[0].startswith('--'):
                rest = rest[1:]
            if rest and rest[0] == target:
                return True
        if Path(value).name == 'cp':
            end = next((j for j in range(index + 1, len(words))
                        if words[j] in ('&&', ';', '||')), len(words))
            if end > index + 1 and words[end - 1] == target:
                return True
    return False


def completed(path, targets):
    rows = {target: [] for target in targets}; last = []
    with gzip.open(path, 'rt', errors='strict') as stream:
        line_number = 0
        while line := stream.readline(2 * 1024 * 1024):
            line_number += 1
            if not line.endswith('\n') and len(line) == 2 * 1024 * 1024:
                # Never accumulate an unrelated enormous printed command.
                while part := stream.readline(2 * 1024 * 1024):
                    if part.endswith('\n'): break
                last = []; continue
            text = line[:-1] if line.endswith('\n') else line
            match = re.match(r'^\[(\d+)/(\d+)\] (.*)$', text)
            if match:
                command = match[3]; last = []
                for target in targets:
                    if target in command and produces(command, target):
                        row = {'line': line_number, 'progress': match[1] + '/' + match[2],
                               'command': command,
                               'sha256': hashlib.sha256(command.encode()).hexdigest()}
                        rows[target].append(row); last.append((target, row))
            elif text.startswith('FAILED: '):
                for target, row in last:
                    if rows[target] and rows[target][-1] is row:
                        rows[target].pop()
                last = []
    return rows


def native_hash(command, rsp=None):
    data = command.encode()
    if rsp:
        data += b'\x1f' + rsp
    return hashlib.sha256(data).hexdigest()


def phases(root, targets):
    root = Path(root); result = []
    for folder in sorted((root / 'attempt/native-evidence').glob('*')):
        receipt = read(folder / 'receipt.json')
        if (receipt['attempt_started_sha256'] != sha(root / 'attempt/started.json') or
                receipt['integration_sha256'] != sha(root / 'attempt/integration.json')):
            raise ValueError('Native evidence attempt binding drift')
        for name, row in receipt['files'].items():
            path = folder / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
                raise ValueError('Frozen native evidence changed: ' + str(path))
        required = {'verbose.log.gz', '.ninja_log', 'siso_metrics.json', 'siso_metadata.json'}
        if not required <= receipt['files'].keys():
            raise ValueError('Missing genuine native phase channels')
        metrics = {}
        with (folder / 'siso_metrics.json').open() as stream:
            for number, line in enumerate(stream, 1):
                row = json.loads(line)
                if row.get('output') in targets:
                    metrics.setdefault(row['output'], []).append({'line': number, 'value': row})
        ninja = {}
        with (folder / '.ninja_log').open() as stream:
            if stream.readline().strip() != '# ninja log v5':
                raise ValueError('Unsupported frozen Ninja log')
            for number, line in enumerate(stream, 2):
                values = line.rstrip('\n').split('\t')
                if len(values) == 5 and values[3] in targets:
                    if not re.fullmatch('[0-9a-f]{1,16}', values[4]) or int(values[4], 16) == 0:
                        raise ValueError('Invalid frozen Ninja command identifier')
                    ninja[values[3]] = {'line': number, 'raw_v5_row': line.rstrip('\n')}
        result.append({'folder': str(folder), 'receipt_sha256': sha(folder / 'receipt.json'),
                       'receipt': receipt, 'metadata': read(folder / 'siso_metadata.json'),
                       'commands': completed(folder / 'verbose.log.gz', targets),
                       'metrics': metrics, 'ninja': ninja})
    return sorted(result, key=lambda row: row['metadata']['start_time'])


def metric_error(metric):
    return bool(metric.get('err') or metric.get('error') or metric.get('exit_code', 0))


def execution(phase, target, expected_cmdhash, aosp, rsp_paths=()):
    metrics = phase['metrics'].get(target, [])
    if not metrics:
        return None
    latest = max(metrics, key=lambda row: row['value'].get('action_end', -1))
    value = latest['value']
    if metric_error(value):
        raise ValueError('Failed native action cannot qualify: ' + target)
    if not {'action_start', 'action_end', 'cmdhash'} <= value.keys():
        raise ValueError('Missing actual native execution fields')
    if base64.b64decode(value['cmdhash']).hex() != expected_cmdhash:
        return None
    if target not in phase['ninja']:
        raise ValueError('Native action lacks frozen Ninja corroboration')
    candidates = []
    for row in phase['commands'].get(target, []):
        if native_hash(row['command']) == expected_cmdhash:
            candidates.append((row, None))
        for relative in rsp_paths:
            path = Path(aosp) / relative
            if path.is_file() and path.stat().st_size <= 4 * 1024 * 1024:
                if native_hash(row['command'], path.read_bytes()) == expected_cmdhash:
                    candidates.append((row, relative))
    if not candidates:
        raise ValueError('Exact completed command/response hash mismatch: ' + target)
    command, rsp = candidates[-1]
    receipt = phase['receipt']
    return {'phase_path': phase['folder'], 'phase_receipt_sha256': phase['receipt_sha256'],
            'phase_exit_code': receipt['exit_code'],
            'attempt_started_sha256': receipt['attempt_started_sha256'],
            'integration_sha256': receipt['integration_sha256'],
            'verbose': command, 'metrics': latest, 'ninja': phase['ninja'][target],
            'command_hash_hex': expected_cmdhash, 'primary_rsp': rsp}


def require_current_closure(root, plan, bundle=None):
    root = Path(root)
    targets = set(read(plan['native_lineage_map'])['records'])
    bundle = phases(root, targets) if bundle is None else bundle
    started = datetime.datetime.fromisoformat(read(root / 'attempt/started.json')['utc'])
    names = {}
    for phase in bundle:
        if phase['receipt']['exit_code'] != 0:
            raise ValueError('Current native phase failed; no final current acceptance')
        when = datetime.datetime.fromisoformat(phase['metadata']['start_time'].replace('Z', '+00:00'))
        if when < started:
            raise ValueError('Current native closure predates this actual attempt')
        names[Path(phase['folder']).name] = set(phase['metadata']['targets'])
    if not {'bpfloader', 'vold'} <= names.get('host_init_verifier', set()):
        raise ValueError('Missing genuine current bpfloader/vold native closure')
    if not {'bootimage', 'systemimage'} <= names.get('bootimage', set()):
        raise ValueError('Missing genuine current bootimage/systemimage native closure')
    return {'scope': 'FINAL_CURRENT_ACCEPTANCE_NATIVE_CLOSURE',
            'phases': [{'path': row['folder'], 'receipt_sha256': row['receipt_sha256']}
                       for row in bundle], 'historical_all_input_bytes_attested': False}
