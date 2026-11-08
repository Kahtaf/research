"""Offline, parent-reviewable evidence selection. No transport or arbitrary paths."""
import importlib.util
import json
from pathlib import Path
import re
from policy import (TARGET, TRANSPORT, SERIAL, REMOTE_BASE, SIZE, BUFFER, Stop, require,
                    valid_run, sha, encoded, digest_file, validate_rows, chunk_layout)

SPIKE = Path(__file__).resolve().parents[1]
WORKSPACE = SPIKE.parent
LEGACY_SPIKE = WORKSPACE/'2026-11-06-asus-stock-system-stream-backup'
LEGACY_RUN = '20261106T155844Z-80cb7ab425df604b'
LEGACY_CODE = {'policy.py': '21c016335b40605ce7f7c2c5c741dcf976fe9b2cf5f6286595b7042fa15cad5c',
               'remote_worker.py': '59f1477ff7af66c6040a8f785afd3803b53b6b96510a0133d977253915e0abfc',
               'stock_system_backup.py': 'cc0ce26e7d310251d6cb7f4202fefca3658e16c5c63277e8830904b1fe0a97d3'}
LEGACY_REVIEW = 'fd3cbe0005540fac152fb0928d8a54471f0c87e4798c3d1d18aa436836ece13c'


def source_directory(run):
    return (LEGACY_SPIKE if run == LEGACY_RUN else SPIKE)/'evidence/runs'/valid_run(run)


def safe_bytes(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/symlink evidence: '+str(path))
    require(path.stat().st_size < 16*1024*1024, 'Evidence exceeds metadata bound')
    return path.read_bytes()


def load_events(directory):
    require(directory.is_dir() and not directory.is_symlink(), 'Missing/unsafe source evidence directory')
    events = []
    for number, path in enumerate(sorted(directory.glob('[0-9][0-9][0-9][0-9][0-9]-*.json')), 1):
        require(path.name.startswith('%05d-' % number), 'Nonsequential journal: '+path.name)
        raw = safe_bytes(path)
        event = json.loads(raw)
        require(path.name == '%05d-%s.json' % (number, event['kind']), 'Journal kind/name mismatch')
        events.append(dict(event=event, path=path, sha256=sha(raw)))
    require(events and events[0]['event']['kind'] == 'plan', 'Missing captured plan')
    return events


def legacy_module():
    for name, expected in LEGACY_CODE.items():
        require(sha(safe_bytes(LEGACY_SPIKE/'source'/name)) == expected, 'Original trusted source changed')
    require(sha(safe_bytes(LEGACY_SPIKE/'evidence/parent-review-shell-v2.json')) == LEGACY_REVIEW,
            'Original parent source-review pin changed')
    spec = importlib.util.spec_from_file_location('reviewed_usb_source', LEGACY_SPIKE/'source/stock_system_backup.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(digest_file(module.HELPER)[1] == module.HELPER_HASH, 'Original helper changed')
    require(digest_file(module.ROOT_BINARY)[1] == module.ROOT_BINARY_HASH, 'Original root binary changed')
    return module


def validate_stage(segment, stage, module, run):
    e = stage['event']
    index = segment.index(stage)
    dispatches = [(i, x['event']) for i, x in enumerate(segment[:index])
                  if x['event']['kind'] == 'dispatch' and x['event'].get('script')]
    require(dispatches, 'No root source-read dispatch')
    pos, dispatch = dispatches[-1]
    script = dispatch['script']
    base = module.BASE if run == LEGACY_RUN else module.BASE+'/'+run
    read = f"dd if={module.BLOCK} of={base}/{e['label']}.bin bs={BUFFER} skip={e['offset']//BUFFER} count={e['bytes']//BUFFER}"
    require(module.DEVICE_GUARD in script and read in script, 'Missing exact captured identity/RO/geometry/read guard')
    require(dispatch['argv'][-1] == str(module.HELPER), 'Source read used untrusted helper')
    # Render the pinned implementation's exact fixed source-read body offline.
    bodies = []
    device = module.Device(run, type('ReceiptOnly', (), {'event': lambda *a, **k: None})())
    def capture(body):
        bodies.append(body)
        return 'ASUS_STAGE_INODE='+str(e['inode'])+'\n'
    device.root = capture
    device.stage(e['label'], e['offset'], e['bytes'])
    require(len(bodies) == 1, 'Unexpected source-read dispatch count')
    returned = segment[pos+1]['event']
    token = re.findall(r'ASUS_SYSTEM_RC_([0-9a-f]{32})=', script)
    require(len(token) == 1 and returned['kind'] == 'returned' and returned['status'] == 0,
            'Root source dispatch completion uncertain')
    require(script == module.root_envelope(bodies[0], token[0]), 'Captured source script differs from pinned implementation')
    status = re.findall(r'^ASUS_SYSTEM_RC_'+token[0]+r'=(\d+)\r?$', returned['stdout'], re.M)
    require(status == ['0'], 'Source operation status not successful')
    inodes = re.findall(r'^ASUS_STAGE_INODE=(\d+)\r?$', returned['stdout'], re.M)
    require(inodes == [str(e['inode'])], 'Source stage inode receipt mismatch')


def validate_capture(segment, row, module, run):
    stages = [x for x in segment if x['event']['kind'] == 'source_read_staged']
    receives = [x for x in segment if x['event']['kind'] == 'binary_received']
    exports = [x for x in segment if x['event']['kind'] == 'binary_dispatch']
    require(len(exports) == 2, 'Missing/duplicate binary dispatch')
    require(len(stages) == len(receives) == 2, 'Missing independent source stages/exports')
    for stage, export, receive, label in zip(stages, exports, receives, ('a', 'b')):
        e, received = stage['event'], receive['event']
        require((e['label'], e['offset'], e['bytes']) == (label, row['offset'], row['bytes']), 'Source slice receipt mismatch')
        require((received['label'], received['bytes']) == (label, row['bytes']), 'Binary export incomplete')
        require((export['event']['label'], export['event']['bytes']) == (label, row['bytes']), 'Binary dispatch mismatch')
        require(segment.index(stage) < segment.index(export) < segment.index(receive), 'Binary receipt precedes source read/export')
        validate_stage(segment, stage, module, run)
    require(segment.index(receives[0]) < segment.index(stages[1]), 'Source captures not independently ordered')
    checks = [x for x in segment if x['event']['kind'] == 'two_source_reads_verified']
    require(len(checks) == 1 and segment.index(receives[1]) < segment.index(checks[0]), 'Missing byte comparison completion')
    check = checks[0]['event']
    require((check['index'], check['bytes']) == (row['index'], row['bytes']), 'Comparison slice mismatch')
    if run == LEGACY_RUN:
        # Pinned original implementation emits this only after exact byte compare,
        # matching both independent digests and full length, and host reread.
        require(check['sha256'] == row['sha256_a'] == row['sha256_b'], 'False comparison receipt')
    else:
        require(check['compared_bytes'] == row['bytes'] and check['sha256_a'] == check['sha256_b'] == row['sha256_a'],
                'False comparison receipt')
    return checks[0]['sha256']


def put_receipt(segment, row, run, uncertain):
    dispatches = [i for i, x in enumerate(segment) if x['event']['kind'] == 'remote_dispatch'
                  and x['event']['request'].get('operation') == 'put']
    require(len(dispatches) == 1, 'Missing/duplicate upload dispatch')
    i = dispatches[0]
    comparisons = [j for j,x in enumerate(segment) if x['event']['kind'] == 'two_source_reads_verified']
    require(len(comparisons) == 1 and comparisons[0] < i, 'Upload precedes byte comparison completion')
    q = segment[i]['event']['request']
    require(q == dict(operation='put', run=run, index=row['index'], bytes=row['bytes'], sha256=row['sha256_a']),
            'Upload dispatch mismatch')
    if uncertain:
        return
    require(i+1 < len(segment), 'Missing upload readback acknowledgement')
    ack = segment[i+1]['event']
    require(ack['kind'] == 'remote_returned' and ack['status'] == 0, 'Unverified upload status')
    require(json.loads(ack['stdout']) == dict(operation='put', run=run, index=row['index'], bytes=row['bytes'], sha256=row['sha256_a']),
            'Upload stored-byte receipt mismatch')


def prepare(run=LEGACY_RUN, include_uncertain=False, lineage=()):
    import stock_system_backup as current
    run = valid_run(run)
    require(run not in lineage and len(lineage) < 112, 'Cyclic/excessive continuation lineage')
    module = legacy_module() if run == LEGACY_RUN else current
    code = LEGACY_CODE if run == LEGACY_RUN else current.local_inputs()
    directory = source_directory(run)
    events = load_events(directory)
    plan = events[0]['event']
    require(plan.get('target') == TARGET and plan.get('run') == run and plan.get('mode') == 'EXECUTE'
            and plan.get('action') == 'backup' and plan.get('no_raw_block_writes') is True,
            'Captured plan identity/geometry/scope mismatch')
    require(plan.get('source_code_sha256') == code and plan.get('helper_sha256') == module.HELPER_HASH
            and plan.get('root_binary_sha256') == module.ROOT_BINARY_HASH, 'Captured source provenance mismatch')
    if run != LEGACY_RUN:
        require(plan.get('transport') == TRANSPORT, 'Captured endpoint/security mismatch')
    rows, start, last = [], 1, 0
    if run != LEGACY_RUN:
        prefix = [(i, x['event']) for i, x in enumerate(events) if x['event']['kind'] == 'prefix_verified']
        require(len(prefix) == 1, 'No completed prefix import; restart from previously reviewed source input')
        last, imported = prefix[0]
        raw = safe_bytes(directory/'input.json')
        require(sha(raw) == plan['reviewed_input_sha256'] == imported['reviewed_input_sha256'], 'Prior input pin mismatch')
        previous = json.loads(raw)
        validate_input(previous, sha(raw), lineage+(run,))
        validate_rows(previous['chunks'])
        require(imported['chunks'] == previous['chunks'] and imported['source_run'] == previous['source_run'], 'False imported prefix')
        returned = events[last-1]['event']
        require(returned['kind'] == 'remote_returned' and returned['status'] == 0, 'Missing prefix rehash receipt')
        receipts = json.loads(returned['stdout'])
        require(receipts.get('operation') == 'reuse' and receipts.get('run') == run and len(receipts['receipts']) == len(imported['chunks']), 'Wrong prefix receipt')
        for row, receipt in zip(imported['chunks'], receipts['receipts']):
            require(receipt['index'] == row['index'], 'Prefix receipt order mismatch')
            for side in ('source', 'copied'):
                require((receipt[side]['bytes'], receipt[side]['sha256']) == (row['bytes'], row['sha256_a']), 'False prefix hash receipt')
        rows = list(imported['chunks'])
        start = last+1
    for i in range(start, len(events)):
        e = events[i]['event']
        if e['kind'] != 'chunk_verified':
            continue
        row = {k: e[k] for k in ('index', 'offset', 'bytes', 'sha256_a', 'sha256_b', 'remote_sha256')}
        require(row['index'] == len(rows), 'Noncontiguous verified receipts')
        segment = events[start:i+1]
        receipt_hash = validate_capture(segment, row, module, run)
        put_receipt(segment, row, run, False)
        origin = dict(run=run, transport=dict(kind='adb-usb', serial=SERIAL) if run == LEGACY_RUN else TRANSPORT,
                      source_code_sha256=code, helper_sha256=module.HELPER_HASH,
                      root_binary_sha256=module.ROOT_BINARY_HASH, receipt_sha256=receipt_hash)
        if run != LEGACY_RUN:
            require(e.get('source_capture') == origin, 'False new capture provenance')
        row['source_capture'] = origin
        rows.append(row)
        last, start = i, i+1
    uncertain = False
    if include_uncertain:
        require(run != LEGACY_RUN, 'Legacy uncertain export is not a completed double capture')
        tail = events[start:]
        intents = [x for x in tail if x['event']['kind'] == 'capture_ready_for_upload']
        require(len(intents) == 1, 'No single completed capture eligible for uncertain-put inspection')
        row = intents[0]['event']['row']
        require(row['index'] == len(rows), 'Uncertain upload is not next contiguous chunk')
        receipt_hash = validate_capture(tail, row, module, run)
        require(row['source_capture'] == dict(run=run, transport=TRANSPORT, source_code_sha256=code,
                helper_sha256=module.HELPER_HASH, root_binary_sha256=module.ROOT_BINARY_HASH, receipt_sha256=receipt_hash),
                'Uncertain capture provenance mismatch')
        put_receipt(tail, row, run, True)
        rows.append(row)
        last, uncertain = len(events)-1, True
    validate_rows(rows)
    pins = {str(x['path'].relative_to(WORKSPACE)): x['sha256'] for x in events[:last+1]}
    if run != LEGACY_RUN:
        pins[str((directory/'input.json').relative_to(WORKSPACE))] = sha(safe_bytes(directory/'input.json'))
    return dict(schema='asus-stock-continuation-input-v1', source_run=run, target=TARGET, chunks=rows,
                captured_plan_sha256=events[0]['sha256'], source_code_sha256=code,
                implementation_sha256=current.local_inputs(), implementation_helper_sha256=current.HELPER_HASH,
                dependency_sha256={str(path.relative_to(WORKSPACE)): digest_file(path)[1] for path in
                                   (module.HELPER, module.ROOT_BINARY, current.HELPER,
                                    WORKSPACE/'2026-11-05-asus-latest-android-feasibility/evidence/live-partition-layout.json')},
                journal_sha256=pins, uncertain_last_put=uncertain,
                trust='Parent must review captured journal origin and unchanged stock since capture; remote bytes always rehashed')


def validate_input(bundle, expected, lineage=()):
    require(sha(encoded(bundle)) == expected, 'Reviewed input pin mismatch')
    require(bundle.get('schema') == 'asus-stock-continuation-input-v1' and bundle.get('target') == TARGET, 'Wrong input scope')
    # Reconstruct from the actual journals, not the proposed rows or offsets.
    actual = prepare(bundle['source_run'], bundle['uncertain_last_put'], lineage)
    require(actual == bundle, 'Actual captured evidence changed since parent review')
    return bundle
