"""Host revision2: resume after the precise BTF filename-offset checker failure."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,resource,struct,subprocess,sys
OWN=Path('/srv/android/asus-radio-trigger-build-r4')
KIT=Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
sys.path.insert(0,str(KIT/'scripts'))
from integrate import read,write,sha,need
from verify_root_payload import verify_ramdisk_properties
from verify_product_r3 import installed
need(os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino==15018964,'Original lock missing')
limits=resource.getrlimit(resource.RLIMIT_AS);need(limits==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'Unlimited host AS required')
need(read(OWN/'attempt/native-terminal.json')['exit']==0 and read(OWN/'attempt/m-exit.json')['exit']==0,'No actual native exit0')
previous=OWN/'checks/r1';o=OWN/'checks/r2';o.mkdir(exist_ok=False)
write(o/'address-space.json',{'soft':limits[0],'hard':limits[1],'unlimited_value':resource.RLIM_INFINITY,'limit_mutation':False})
plan=read(OWN/'inputs/plan.json');a=Path(plan['aosp']);p=Path(plan['product_out']);b=a/'out/host/linux-x86/bin'
report=read(previous/'native-images.json');raw=OWN/'system-partition.raw';completed_raw=OWN/'raw-complete.json'
raw_receipt=read(completed_raw)
need(raw_receipt['sha256']=='fff09d5ab4e0ca301786830d133106152c4c0aca15a2c49166c28827aa5e3f79' and raw.stat().st_size==3753902080 and raw_receipt['source_system_sha256']==report['system']['sha256'],'Existing sole raw identity differs')
raw.chmod(0o444)
apex=previous/'apex';need((apex/'apex-info-list.xml').exists(),'Existing actual APEX extraction missing')
root=read(previous/'root.json');google=read(previous/'google-signed.json');recovery_preservation=read(previous/'custom-recovery-preservation.json')
radio_installed=read(previous/'radio-trigger.json')['final_installed_bytes'];runtime_sha=read(previous/'runtime-linkerconfig.json')['runtime_elf_sha256']
config_path=previous/'embedded-kernel.config'
partition={'system':p/'system','vendor':p/'system/vendor','product':p/'system/product','system_ext':p/'system/system_ext'}
odm=p/'system/vendor/odm'
if not odm.exists():odm=previous/'empty-odm'
need(odm.exists(),'Previously selected odm path missing')
tools=Path(plan['staging'])/'full-boot-tools/scripts'
spec=importlib.util.spec_from_file_location('bootformat',OWN/'scripts/owned_bootformat.py');reader=importlib.util.module_from_spec(spec);sys.modules['bootformat']=reader;spec.loader.exec_module(reader)
sys.path.insert(0,str(tools));import package_full_boot as packager
source_boot=(p/'boot.img').read_bytes();need(hashlib.sha256(source_boot).hexdigest()==report['boot']['sha256'],'BOOT changed after actual validation')
_,kernel_bytes,ramdisk_bytes,_=packager.components(source_boot);qualified_kernel=Path(plan['device'])/'prebuilt/Image.gz-dtb'
commands=[]
def run(argv,label,required=True):
 log=o/(label+'.log');argv=list(map(str,argv))
 with log.open('xb') as f:result=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
 row={'argv':argv,'exit':result.returncode,'log':str(log),'log_sha256':sha(log)}
 commands.append(row);write(o/('commands-'+str(len(commands))+'.json'),commands)
 if required:need(result.returncode==0,'Critical check failed: '+str(log))
 return row
write(o/'resumed-evidence.json',{'actual_native_exit':0,'raw_reused':str(raw),'raw_materializations_total':1,'raw_not_rehashed_or_recreated':True,'apex_reused':str(apex),'prior_passed_checks':{n:sha(previous/n) for n in ['native-images.json','root.json','google-signed.json','google-transformed.json','runtime-linkerconfig.json','radio-trigger.json','custom-recovery-preservation.json']},'failed_host_r1_log_sha256':sha(OWN/'logs/postbuild-r1.log'),'correction':'Resolve only the two pinned identical-source BTF filename spellings; retain every BTF type/name/line/reference/instruction offset, loader section, relocation and symbol assertion'})

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
    from bpf_equivalence import canonical_btf
    btf=canonical_btf({name:bytes.fromhex(sections.pop(name)) for name in ('.BTF','.BTF.ext')})
    return {'sections': sections, 'symbols': sorted(symbols, key=str), 'resolved_btf':btf}
filter_candidates = [f for f in [p / 'system/vendor/etc/bpf/filterPowerSupplyEvents.o', p / 'system/etc/bpf/filterPowerSupplyEvents.o'] if f.is_file()]
need(len(filter_candidates) == 1, 'Final health filter missing/ambiguous')
filter_file = filter_candidates[0]; filter_sha = sha(filter_file)
qualified_sha = 'dc98c75e594dc015d6adca31b23cbea064abae66594dbc92764aeb8389d21904'
equivalence = 'EXACT_ELF_BYTES'
if filter_sha != qualified_sha:
    candidate = Path('/srv/android/asus-linux49-power-supply-filter-20261106/artifacts/postimage.o')
    need(sha(candidate) == qualified_sha, 'Qualified filter reference changed')
    need(bpf_semantics(filter_file) == bpf_semantics(candidate), 'Actual filter program/loader metadata differs from qualified candidate')
    equivalence = 'EXACT_PROGRAM_LOADER_SECTIONS_SYMBOLS_AND_RESOLVED_BTF'
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
command += ['--kernel', str(release) + ':' + str(config_path), '--property', 'ro.product.first_api_level=23',
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
      'kernel_sha256': sha(qualified_kernel), 'embedded_config_sha256': sha(config_path),
      'radio_trigger':radio_installed, 'root_properties': root['generated_security_properties'], 'google_signed_payloads_checked': len(google['checked']),
      'runtime_linkerconfig_sha256': runtime_sha, 'filter_sha256': filter_sha, 'filter_equivalence': equivalence,
      'netd_pair': netd, 'actual_vintf': vintf, 'vintf_passed': vintf['exit'] == 0,
      'policy_neverallows': 'Normal native build dependency checks retained; no ignore flags',
      'old_raw_rehashed': False, 'historical_61_row_or_source_sweep_performed': False,
      'physical_boot_verified': False, 'whole_os_flash_go': False}
write(o / 'critical-checks.json', result)
if not (OWN / 'critical-checks.json').exists(): write(OWN / 'critical-checks.json', result)
print(json.dumps(result), flush=True)
