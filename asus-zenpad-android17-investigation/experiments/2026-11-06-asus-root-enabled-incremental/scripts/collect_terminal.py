"""Compact final readbacks only; never relaunches an attempt or materializes images."""
from pathlib import Path
import collections
import json
import os
import resource
import signal
import struct
import sys

resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
signal.alarm(180)
ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-root-enabled-incremental-r1')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import read, sha, write, need, acquire, verify_pins, manifest
plan = read(ROOT / 'inputs/plan.json')
lock = acquire(plan)
need(os.fstat(lock.fileno()).st_ino == 15018964, 'Original lock drift')
need((OWN / 'attempt/FAILED.json').exists() or (OWN / 'attempt/host-assembly-complete.json').exists(), 'Attempt not terminal')
HOST = OWN / 'host-r2'
result = {'status': 'ROOT_ENABLED_HOST_ASSEMBLY_COMPLETE_COMPATIBILITY_INCOMPLETE' if (HOST / 'complete.json').exists() else 'FAILED',
          'first_host_receipt_comparison_failure_preserved': (OWN / 'attempt/FAILED.json').exists(),
          'original_r9_overall_exit': int(Path(plan['logs'], 'full-build-r9.exit-code').read_text()),
          'original_native_phase_exits': {name: read(ROOT / 'attempt/native-evidence' / name / 'receipt.json')['exit_code']
                                         for name in ('host_init_verifier', 'bootimage')},
          'original_kit_seal': verify_pins(ROOT), 'lock_inode': os.fstat(lock.fileno()).st_ino,
          'source_mk_sha256': sha(Path(plan['device']) / 'lineage_p00a.mk'),
          'old_raw_system': {}, 'overall_validation_passed': False, 'compatibility_incomplete': True,
          'device_accessed': False, 'runtime_verified': False, 'physical_boot_verified': False, 'flash_ready': False}
oldraw = Path('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw')
result['old_raw_system'] = {'path': str(oldraw), 'sha256': sha(oldraw), 'bytes': oldraw.stat().st_size,
                            'mode': oct(oldraw.stat().st_mode & 0o777)}
need(result['old_raw_system']['sha256'] == 'baa69560ace09a478c902077d8ff926d7a079ecb9b9f1632e4c330169b243798' and
     oldraw.stat().st_mode & 0o222 == 0, 'Old raw image changed')
result['receipts'] = {}
for folder in (OWN / 'attempt', OWN / 'validation', HOST, HOST / 'validation'):
    if not folder.exists():
        continue
    for p in folder.glob('*.json'):
        row = {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
        if p.name == 'preservation.json':
            row['preserved_file_count'] = len(read(p)['files'])
        elif p.name == 'r8-product-provenance.json':
            data = read(p)
            row['summary'] = {'payloads': len(data['payloads']), 'admitted_native_outputs': len(data['admitted_native_outputs']),
                              'actual_execution_cohorts': dict(collections.Counter(x.get('actual_execution_cohort', x['provenance_kind'])
                                          for x in data['admitted_native_outputs'].values())),
                              'native_closure': data['native_command_channel_receipts']['current_native_closure']}
        elif p.stat().st_size < 100000:
            row['value'] = read(p)
        result['receipts'][str(p.relative_to(OWN))] = row
native_receipt = OWN / 'attempt/native-evidence/selected-images/receipt.json'
if native_receipt.exists():
    meta = read(native_receipt.with_name('siso_metadata.json'))
    result['actual_selected_native_phase'] = {'receipt': read(native_receipt), 'receipt_sha256': sha(native_receipt),
        'metadata': {k: v for k, v in meta.items() if k in ('start_time', 'end_time', 'targets', 'jobs', 'parallelism')}}
complete_path = HOST / 'validation/complete.json'
if complete_path.exists():
    complete = read(complete_path)
    result['root_route_accepted'] = complete['root_route_accepted']
    result['new_raw_system'] = complete['raw_system']
    raw = Path(complete['raw_system']['path'])
    need(sha(raw) == complete['raw_system']['sha256'], 'New raw drift')
    result['new_raw_system']['allocated_bytes'] = raw.stat().st_blocks * 512
    result['new_raw_system']['mode'] = oct(raw.stat().st_mode & 0o777)
    boot = Path(complete['boot']['path'])
    need(sha(boot) == complete['boot']['sha256'], 'New packaged BOOT drift')
    boot.chmod(0o444)
    image = boot.read_bytes()
    ks, ka, rs, ra, ss, sa, ta, page = struct.unpack_from('<8I', image, 8)
    result['new_mtkboot'] = {'path': str(boot), 'sha256': sha(boot), 'bytes': len(image),
           'header_version': struct.unpack_from('<I', image, 40)[0], 'page_bytes': page,
           'kernel_bytes': ks, 'kernel_address': hex(ka), 'ramdisk_bytes': rs, 'ramdisk_address': hex(ra),
           'second_bytes': ss, 'second_address': hex(sa), 'tags_address': hex(ta)}
native_images = read(OWN / 'logs/full-build-root-enabled-r1.images.json')
result['source_native_images'] = {k: native_images[k] for k in ('boot', 'system')}
result['native_build_executed_once'] = True
result['host_revision_code_pins_sha256'] = sha(HOST / 'inputs/code-pins.json')
result['new_materialized_raw_count'] = sum(1 for p in OWN.rglob('system-partition.raw'))
result['owned_allocation_bytes'] = sum(p.lstat().st_blocks * 512 for p in OWN.rglob('*'))
result['log_tails'] = {}
for p in [*(OWN / 'logs').glob('*.log'), *HOST.glob('*.log')]:
    with p.open('rb') as stream:
        stream.seek(max(0, p.stat().st_size - 6000))
        result['log_tails'][p.name] = {'sha256': sha(p), 'bytes': p.stat().st_size,
                                      'tail': stream.read().decode(errors='replace')}
write(OWN / 'terminal-readback.json', result)
print(json.dumps(result))
