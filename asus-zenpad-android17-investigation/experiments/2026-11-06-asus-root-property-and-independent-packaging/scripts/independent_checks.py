"""Independent VINTF, packaging and source checks; root remains failed."""
from pathlib import Path
import fcntl
import json
import os
import struct
import subprocess
import sys
import traceback

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-r9-independent-packaging-r1')
sys.path.insert(0, str(ROOT / 'scripts'))
from integrate import need, sha, read, write, manifest, verify_integrated
from verify_root_payload import verify_ramdisk_properties

fd = int(os.environ['REVIEWED_BUILD_LOCK_FD'])
need(os.fstat(fd).st_ino == 15018964, 'Wrong inherited lock')
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
plan = read(ROOT / 'inputs/plan.json')
for path, expected in plan['external_pins'].items():
    need(sha(path) == expected, 'Reviewed external input changed: ' + path)
a = Path(plan['aosp'])
p = Path(plan['product_out'])
b = a / 'out/host/linux-x86/bin'
integration = read(ROOT / 'attempt/integration.json')
config = Path(integration['generated_defconfig']['path'])
release = Path(integration['kernel_release']['path'])
prior = read('/srv/android/asus-r9-postbuild-validation-r3/terminal-gate.json')
reuse = read('/srv/android/asus-r9-postbuild-validation-r3/reuse-and-sensor-metadata.json')
raw = Path(reuse['raw_system']['path'])
apex = Path(reuse['reused_apex']['path'])
need(sha(raw) == prior['raw_system']['sha256'] and raw.stat().st_size == 3753902080, 'Raw image drift')
need(manifest(apex) == reuse['reused_apex']['manifest'], 'APEX extraction drift')
need(sha(p / 'system/build.prop') == prior['final_raw_build_prop']['sha256'], 'Root failure input changed')
need(sha(config) == integration['generated_defconfig']['sha256'] and sha(release) == integration['kernel_release']['sha256'], 'Kernel metadata drift')
o = OWN / 'checks'
o.mkdir()
phases = {}

def phase(name, fn):
    try:
        value = fn()
        phases[name] = {'passed': True, 'result': value}
    except Exception as e:
        log = o / (name + '-failure.log')
        with log.open('x') as f:
            traceback.print_exc(file=f)
        phases[name] = {'passed': False, 'error_type': type(e).__name__, 'error': str(e),
                        'log': str(log), 'log_sha256': sha(log)}
    write(o / (name + '-receipt.json'), phases[name])

def vintf():
    partition = {'system': p / 'system', 'vendor': p / 'system/vendor',
                 'product': p / 'system/product', 'system_ext': p / 'system/system_ext'}
    odm = partition['vendor'] / 'odm'
    if not odm.exists():
        odm = o / 'empty-odm'
        odm.mkdir()
    dirmap = {**{'/' + label: path for label, path in partition.items()}, '/odm': odm, '/apex': apex}
    command = [b / 'checkvintf', '--check-compat']
    for label, path in dirmap.items():
        command += ['--dirmap', label + ':' + str(path)]
    command += ['--kernel', str(release) + ':' + str(config), '--property', 'ro.product.first_api_level=23',
                '--property', 'ro.boot.product.hardware.sku=', '--property', 'ro.boot.product.vendor.sku=']
    log = o / 'checkvintf.log'
    with log.open('xb') as f:
        result = subprocess.run(list(map(str, command)), stdout=f, stderr=subprocess.STDOUT, timeout=180)
    receipt = {'argv': list(map(str, command)), 'exit': result.returncode, 'log': str(log),
               'log_sha256': sha(log), 'tool_sha256': sha(b / 'checkvintf')}
    write(o / 'checkvintf-command.json', receipt)
    need(result.returncode == 0, 'Independent checkvintf failed; preserved ' + str(log))
    return receipt

phase('vintf', vintf)
tools = Path(plan['staging']) / 'full-boot-tools/scripts'
sys.path.insert(0, str(tools))
import package_full_boot as packager
source_boot = (p / 'boot.img').read_bytes()
report = read(Path(plan['logs']) / 'full-build-r9.images.json')
kernel = Path(plan['staging']) / 'product-device/prebuilt/Image.gz-dtb'

def packaging():
    packed, dtb, receipt = packager.package(source_boot, kernel.read_bytes(), report, synthetic=False)
    need(receipt['compiled_config_sha256'] == sha(config), 'Packaged embedded config mismatch')
    need(receipt['header_cmdline_bytes'] == 92 and receipt['ramdisk']['synthetic_nonbootable'] is False, 'Wrong full BOOT contract')
    boot = o / 'UNTESTED-ROOT-ROUTE-FAILED-sdk37-combined-boot.img'
    with boot.open('xb') as f:
        f.write(packed)
        f.flush()
        os.fsync(f.fileno())
    with (o / 'packaged.dtb').open('xb') as f:
        f.write(dtb)
    need(sha(boot) == receipt['image_sha256'], 'Final BOOT write mismatch')
    _, wrapped_kernel, wrapped_ramdisk, cmdline = packager.components(packed)
    ks, ka, rs, ra, ss, sa, ta, page = struct.unpack_from('<8I', packed, 8)
    receipt.update({'image_path': str(boot), 'dtb_path': str(o / 'packaged.dtb'),
                    'root_route_accepted': False, 'overall_validation_passed': False,
                    'physical_boot_verified': False, 'flash_ready': False,
                    'header': {'magic': packed[:8].decode(), 'kernel_bytes_including_wrapper': ks,
                               'kernel_address': hex(ka), 'ramdisk_bytes_including_wrapper': rs,
                               'ramdisk_address': hex(ra), 'second_bytes': ss, 'second_address': hex(sa),
                               'tags_address': hex(ta), 'page_bytes': page,
                               'header_version': struct.unpack_from('<I', packed, 40)[0],
                               'component_id_hex': packed[576:608].hex(), 'cmdline': cmdline.decode()},
                    'actual_mtk_wrapper_names': [wrapped_kernel[8:40].split(b'\0')[0].decode(), wrapped_ramdisk[8:40].split(b'\0')[0].decode()]})
    write(o / 'packaging.json', receipt)
    return receipt

phase('packaging', packaging)

def ramdisk_properties():
    entries = packager.parse_cpio(packager.ungzip(packager.components(source_boot)[2])[0])
    result = verify_ramdisk_properties(entries, p)
    write(o / 'ramdisk-properties.json', result)
    return result

phase('ramdisk-properties', ramdisk_properties)

def sources():
    result = verify_integrated(plan, baseline=True)
    write(o / 'source-postimages.json', result)
    return {'path': str(o / 'source-postimages.json'), 'sha256': sha(o / 'source-postimages.json')}

phase('source-postimages', sources)
write(o / 'independent-results.json', {'phases': phases,
      'root_route': {'accepted': False, 'failure': prior['gate'], 'observed_ro_debuggable': '0', 'required_ro_debuggable': '1',
                     'prior_receipt_sha256': sha('/srv/android/asus-r9-postbuild-validation-r3/terminal-gate.json')},
      'raw_system': prior['raw_system'], 'apex_reused': str(apex), 'original_r9_overall_exit': 1,
      'original_native_phase_exits': {'host_init_verifier': 0, 'bootimage': 0},
      'overall_validation_passed': False, 'runtime_verified': False, 'physical_boot_verified': False, 'flash_ready': False})
print(json.dumps({'phase_results': {k: v['passed'] for k, v in phases.items()}, 'overall_validation_passed': False}), flush=True)
