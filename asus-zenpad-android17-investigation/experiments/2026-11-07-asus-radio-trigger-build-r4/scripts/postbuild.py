"""Critical final-image checks only; prior runtime qualification is byte-bound."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import os
import resource
import struct
import subprocess
import sys

OWN = Path('/srv/android/asus-radio-trigger-build-r4')
KIT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0, str(KIT / 'scripts'))
from integrate import read, write, sha, need
from verify_full_images import inspect_boot, inspect_system
from verify_google_payload import verify as verify_google
from verify_google_transformed import verify as verify_google_transformed
from verify_root_payload import verify as verify_root, verify_ramdisk_properties
from verify_product_r3 import installed
limits=resource.getrlimit(resource.RLIMIT_AS)
write(OWN/'attempt/postbuild-address-space.json',{'soft':limits[0],'hard':limits[1],'unlimited_value':resource.RLIM_INFINITY,'limit_mutation':False})
need(limits==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'Postbuild AS must inherit unlimited')
plan = read(OWN / 'inputs/plan.json')
a = Path(plan['aosp']); p = Path(plan['product_out']); b = a / 'out/host/linux-x86/bin'
need(os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino == 15018964, 'Original lock not inherited')
need(read(OWN / 'attempt/native-terminal.json')['exit'] == 0, 'No genuine native success')
revision = sys.argv[1] if len(sys.argv) > 1 else 'r1'
o = OWN / 'checks' / revision; o.mkdir(parents=True, exist_ok=False)
commands = []
def run(argv, label, required=True):
    log = o / (label + '.log')
    argv = list(map(str, argv))
    with log.open('xb') as f: result = subprocess.run(argv, stdout=f, stderr=subprocess.STDOUT)
    row = {'argv': argv, 'exit': result.returncode, 'log': str(log), 'log_sha256': sha(log)}
    commands.append(row); write(o / ('commands-' + str(len(commands)) + '.json'), commands)
    if required: need(result.returncode == 0, 'Critical check failed: ' + str(log))
    return row

report = {'boot': inspect_boot(p / 'boot.img', 16740352, 'e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'),
          'system': inspect_system(p / 'system.img', 3753902080)}
write(o / 'native-images.json', report)
tools = Path(plan['staging']) / 'full-boot-tools/scripts'
spec = importlib.util.spec_from_file_location('bootformat', OWN / 'scripts/owned_bootformat.py')
reader = importlib.util.module_from_spec(spec); sys.modules['bootformat'] = reader; spec.loader.exec_module(reader)
sys.path.insert(0, str(tools)); import package_full_boot as packager
source_boot = (p / 'boot.img').read_bytes()
_, kernel_bytes, ramdisk_bytes, _ = packager.components(source_boot)
qualified_kernel = Path(plan['device']) / 'prebuilt/Image.gz-dtb'
need(sha(qualified_kernel) == 'e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1' and kernel_bytes == qualified_kernel.read_bytes(), 'Qualified Image input changed')
embedded = packager.kernel_config(packager.ungzip(kernel_bytes)[0])
need(hashlib.sha256(embedded).hexdigest() == '10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2', 'Embedded kernel config mismatch')
with (o / 'embedded-kernel.config').open('xb') as f: f.write(embedded)

# Exactly one new raw; explicit later host corrections reuse it without rematerialization.
raw = OWN / 'system-partition.raw'
completed_raw = OWN / 'raw-complete.json'
if completed_raw.exists():
    receipt = read(completed_raw)
    need(receipt['source_system_sha256'] == report['system']['sha256'] and sha(raw) == receipt['sha256'], 'Existing raw belongs to another image or changed')
else:
    need(not (OWN / 'raw-reservation.json').exists(), 'Incomplete raw creation preserved; do not duplicate')
    write(OWN / 'raw-reservation.json', {'source_system_sha256': report['system']['sha256'], 'path': str(raw)})
    sparse = report['system']['sparse']
    expanded = OWN / 'expanded-system.tmp'
    if sparse: run([b / 'simg2img', p / 'system.img', expanded], 'simg2img')
    source = expanded if sparse else p / 'system.img'
    need(source.stat().st_size <= 3753902080, 'Expanded image exceeds partition')
    with source.open('rb') as src, raw.open('xb') as dst:
        count = 0
        for data in iter(lambda: src.read(1024 * 1024), b''): dst.write(data); count += len(data)
        zero = bytes(1024 * 1024)
        while count < 3753902080:
            data = zero[:min(len(zero), 3753902080 - count)]; dst.write(data); count += len(data)
        dst.flush(); os.fsync(dst.fileno())
    if sparse: expanded.unlink()
    need(raw.stat().st_size == 3753902080, 'Wrong raw partition length')
    write(completed_raw, {'path': str(raw), 'bytes': raw.stat().st_size, 'sha256': sha(raw),
          'source_system_sha256': report['system']['sha256'], 'all_zero_ranges_written': True})
run([b / 'e2fsck', '-f', '-n', raw], 'e2fsck')
# Custom-recovery preservation: six bounded raw directory-entry checks only.
recovery_paths=['/system/bin/install-recovery.sh','/system/etc/install-recovery.sh',
 '/system/vendor/bin/install-recovery.sh','/system/vendor/etc/install-recovery.sh',
 '/system/vendor/etc/recovery.img','/system/vendor/recovery-from-boot.p']
recovery_rows=[]
import re
for index,path in enumerate(recovery_paths):
 result=subprocess.run([str(b/'debugfs'),'-R','stat '+path,str(raw)],capture_output=True,text=True)
 text=result.stdout+'\n'+result.stderr
 row={'path':path,'stat_exit':result.returncode,'stat_output':text,'present':None}
 if 'File not found by ext2_lookup' in text:row['present']=False
 elif re.search(r'Inode:\s*\d+',text):
  row['present']=True
  size=re.search(r'(?<!Block )Size:\s*(\d+)',text)
  row['bytes']=int(size.group(1)) if size else None
  if path.endswith('.sh') and row['bytes'] is not None and row['bytes']<=65536 and 'Type: regular' in text:
   bounded=o/('recovery-script-'+str(index)+'.txt')
   dump=subprocess.run([str(b/'debugfs'),'-R','dump '+path+' '+str(bounded),str(raw)],capture_output=True,text=True)
   row['dump_exit']=dump.returncode
   if bounded.exists():
    row['contents_sha256']=sha(bounded);row['bounded_contents']=bounded.read_bytes()[:16384].decode(errors='replace')
    row['contents_truncated']=bounded.stat().st_size>16384
  row['bounded_review_required']=True
 else:row['stat_interpretation']='UNRESOLVED_DIRECTORY_ENTRY_QUERY'
 recovery_rows.append(row)
recovery_preservation={'expected_paths':recovery_rows,'all_expected_absent':all(x['present'] is False for x in recovery_rows),
 'filename_alone_treated_as_failure':False,'present_script_requires_bounded_content_interpretation':any(x['present'] is True for x in recovery_rows),
 'recovery_refresh_service_changed':False,'native_rebuild_for_recovery_service':False,'physical_p10_accessed':False}
write(o/'custom-recovery-preservation.json',recovery_preservation)

partition = {'system': p / 'system', 'vendor': p / 'system/vendor', 'product': p / 'system/product', 'system_ext': p / 'system/system_ext'}
apex = o / 'apex'; apex.mkdir()
odm = p / 'system/vendor/odm'
if not odm.exists(): odm = o / 'empty-odm'; odm.mkdir()
command = [b / 'apexd_host', '--tool_path', a / 'out/host/linux-x86', '--apex_path', apex]
for name, path in {**partition, 'odm': odm}.items(): command += ['--' + name + '_path', path]
run(command, 'actual-apex-extraction')

radio_source=a/'device/asus/p00a/radio/init.p00a-radio.rc'
need(sha(radio_source)=='f618fdbaa7d8c659b5edc4dbcf1b21bf30f3525a08c1f88d17ed873b02a23f71','Final radio source identity differs')
radio_installed=installed(p,'system/vendor/etc/init/init.p00a-radio.rc',raw,b/'debugfs','f618fdbaa7d8c659b5edc4dbcf1b21bf30f3525a08c1f88d17ed873b02a23f71')
write(o/'radio-trigger.json',{'source_sha256':sha(radio_source),'final_installed_bytes':radio_installed,'runtime_radio_working_claimed':False})
root = verify_root(p, apex, read(KIT / 'inputs/root-source-pins.json')['packages/modules/adb/root/adb_root.rc'], raw, b / 'debugfs')
write(o / 'root.json', root)
google = verify_google(read(KIT / 'inputs/google-inline-source-manifest.json'), p, raw, b / 'debugfs')
need(len(google['checked']) == 30, 'Google signed payload coverage incomplete')
write(o / 'google-signed.json', google)
transformed = verify_google_transformed(read(KIT / 'inputs/google-inline-source-manifest.json'), p, raw, b / 'debugfs', Path(plan['readobj']).with_name('llvm-readelf'), a)
write(o / 'google-transformed.json', transformed)

# Bind the actual newly extracted runtime APEX ELF to the ordinary native leaf and source.
namespace_source = a / 'system/linkerconfig/contents/namespace/systemdefault.cc'
need(sha(namespace_source) == 'e2aa65d9382f2f0e5c7600e5312046e4236ec2b7b1e108fa5cc12bd7d911f3c8', 'Repaired namespace source changed')
runtime = apex / 'com.android.runtime/bin/linkerconfig'; runtime_sha = sha(runtime)
leaf_root = a / 'out/soong/.intermediates/system/linkerconfig/linkerconfig'
matches = [str(f) for f in leaf_root.rglob('linkerconfig') if f.is_file() and sha(f) == runtime_sha]
need(matches and runtime_sha != 'f697b2f950e3693449989cfc3e1c94ae9845f48dc9ff1e9af271b01a815bd157', 'Runtime APEX still has old/unbound linkerconfig')
fresh_compile = []
verbose = OWN / 'attempt/native-evidence/selected-images/verbose.log.gz'
with gzip.open(verbose, 'rt') as stream:
    for line in stream:
        if 'system/linkerconfig/contents/namespace/systemdefault.cc' in line and ' -c ' in line:
            fresh_compile.append({'command_sha256': hashlib.sha256(line.encode()).hexdigest(), 'command_tail': line[-1800:]})
# Record current compile evidence when present; ordinary accepted dependency tracking also permits cache reuse.
archive_matches = [f for f in (p / 'system/apex').glob('com.android.runtime.*') if f.suffix in ('.apex', '.capex')]
need(len(archive_matches) == 1, 'Runtime APEX container ambiguous')
runtime_container = installed(p, str(archive_matches[0].relative_to(p)), raw, b / 'debugfs')
write(o / 'runtime-linkerconfig.json', {'runtime_elf_sha256': runtime_sha, 'source_sha256': sha(namespace_source),
      'ordinary_native_byte_matches': matches, 'fresh_compile_evidence': fresh_compile, 'container': runtime_container,
      'actual_apex_metadata_sha256': sha(apex / 'apex-info-list.xml'), 'old_isolated_checker_executed': False,
      'matches_qualified_target_candidate': runtime_sha == 'cb03a693acab8781ffa9ee4ccaca3ecd4967bd985ff87db3a23af14e5357c573'})

def bpf_semantics(path):
    data = Path(path).read_bytes()
    need(data[:6] == b'\x7fELF\x02\x01', 'Expected ELF64 BPF object')
    offset = struct.unpack_from('<Q', data, 40)[0]
    width, count, names_index = struct.unpack_from('<HHH', data, 58)
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, offset + i * width) for i in range(count)]
    names_header = headers[names_index]; names = data[names_header[4]:names_header[4] + names_header[5]]
    def string(table, at): return table[at:table.find(b'\0', at)].decode()
    section_names = [string(names, h[0]) for h in headers]
    sections = {}
    symbols = []
    for index, h in enumerate(headers):
        name = section_names[index]
        if h[1] in (1, 4, 9) and not name.startswith('.debug') and name not in ('.comment', '.llvm_addrsig'):
            sections[name] = data[h[4]:h[4] + h[5]].hex()
        if h[1] == 2:
            strings_h = headers[h[6]]; strings = data[strings_h[4]:strings_h[4] + strings_h[5]]
            for at in range(h[4], h[4] + h[5], h[9]):
                n, info, other, section, value, size = struct.unpack_from('<IBBHQQ', data, at)
                if info & 15 == 4: continue  # STT_FILE is compiler debug provenance, not loader metadata.
                symbols.append((string(strings, n), info, other, section_names[section] if section < count else section, value, size))
    return {'sections': sections, 'symbols': sorted(symbols, key=str)}
filter_candidates = [f for f in [p / 'system/vendor/etc/bpf/filterPowerSupplyEvents.o', p / 'system/etc/bpf/filterPowerSupplyEvents.o'] if f.is_file()]
need(len(filter_candidates) == 1, 'Final health filter missing/ambiguous')
filter_file = filter_candidates[0]; filter_sha = sha(filter_file)
qualified_sha = 'dc98c75e594dc015d6adca31b23cbea064abae66594dbc92764aeb8389d21904'
equivalence = 'EXACT_ELF_BYTES'
if filter_sha != qualified_sha:
    candidate = Path('/srv/android/asus-linux49-power-supply-filter-20261106/artifacts/postimage.o')
    need(sha(candidate) == qualified_sha, 'Qualified filter reference changed')
    need(bpf_semantics(filter_file) == bpf_semantics(candidate), 'Actual filter program/loader metadata differs from qualified candidate')
    equivalence = 'EXACT_PROGRAM_LOADER_SECTIONS_AND_SYMBOLS'
filter_image = installed(p, str(filter_file.relative_to(p)), raw, b / 'debugfs', filter_sha)
write(o / 'health-filter.json', {'actual_sha256': filter_sha, 'qualified_sha256': qualified_sha,
      'qualification_binding': equivalence, 'final_image_bytes': filter_image, 'kernel_tests_repeated': False,
      'critical_healthd_and_loader_metadata_retained': True})
netd = {}
for filename, expected in [('netd.o', '863f3d2e79e804559c90ec145f23210d48f841777bb646a5f3f4b45952aad4b8'),
                           ('netd@funcs.o', 'b5f8f4bf79dfbd6403405163b768a3307b43fd30d90b19ac3fd2260d746ff9c4')]:
    files = list({f.resolve(): f for f in apex.glob('*/etc/bpf/' + filename)}.values())
    need(len(files) == 1 and sha(files[0]) == expected, 'Qualified final netd pair changed: ' + filename)
    netd[filename] = {'path': str(files[0]), 'sha256': expected, 'previous_runtime_qualification_reused': True}
write(o / 'netd-binding.json', netd)

release = Path(plan['kernel_release'])
command = [b / 'checkvintf', '--check-compat']
for name, path in {**partition, 'odm': odm, 'apex': apex}.items(): command += ['--dirmap', '/' + name + ':' + str(path)]
command += ['--kernel', str(release) + ':' + str(o / 'embedded-kernel.config'), '--property', 'ro.product.first_api_level=23',
            '--property', 'ro.boot.product.hardware.sku=', '--property', 'ro.boot.product.vendor.sku=']
vintf = run(command, 'actual-checkvintf', required=False)
packed, dtb, packaging = packager.package(source_boot, qualified_kernel.read_bytes(), report, synthetic=False)
packaging['ramdisk_properties'] = verify_ramdisk_properties(packager.parse_cpio(packager.ungzip(ramdisk_bytes)[0]), p)
need(packaging['compiled_config_sha256'] == '10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2', 'Packaged config mismatch')
boot = o / 'UNTESTED-combined-MTKBOOT.img'
with boot.open('xb') as f: f.write(packed); f.flush(); os.fsync(f.fileno())
with (o / 'packaged.dtb').open('xb') as f: f.write(dtb)
need(sha(boot) == packaging['image_sha256'], 'Final packaged bytes mismatch')
raw.chmod(0o444); boot.chmod(0o444)
write(o / 'packaging.json', packaging)
result = {'native_exit': 0, 'custom_recovery_preservation':recovery_preservation, 'critical_image_checks_passed': True, 'root_route_accepted': True,
      'source_images': report, 'new_raw_system': read(completed_raw),
      'mtkboot': {'path': str(boot), 'bytes': boot.stat().st_size, 'sha256': sha(boot)},
      'kernel_sha256': sha(qualified_kernel), 'embedded_config_sha256': sha(o / 'embedded-kernel.config'),
      'radio_trigger':radio_installed, 'root_properties': root['generated_security_properties'], 'google_signed_payloads_checked': len(google['checked']),
      'runtime_linkerconfig_sha256': runtime_sha, 'filter_sha256': filter_sha, 'filter_equivalence': equivalence,
      'netd_pair': netd, 'actual_vintf': vintf, 'vintf_passed': vintf['exit'] == 0,
      'policy_neverallows': 'Normal native build dependency checks retained; no ignore flags',
      'old_raw_rehashed': False, 'historical_61_row_or_source_sweep_performed': False,
      'physical_boot_verified': False, 'whole_os_flash_go': False}
write(o / 'critical-checks.json', result)
if not (OWN / 'critical-checks.json').exists(): write(OWN / 'critical-checks.json', result)
print(json.dumps(result), flush=True)
