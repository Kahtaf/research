from pathlib import Path
import hashlib,json,subprocess,os,difflib,gzip,shutil,re
R=Path('/srv/android/asus-bmc156-accelerometer-r1');K=R/'kernel';B=Path('/srv/android/asus-build-continuation');A=Path('/srv/android/lineage24');E=R/'evidence'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def config(p):
 out={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):key,val=l.split('=',1);out[key]=val
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):out[l.split()[1]]='n'
 return out
base=json.loads((E/'baseline-source-hashes.json').read_text());changes={}
# Verify every baseline file in the original physical source and own fixture.
for rel,h in base.items():
 assert sha(B/'kernel'/rel)==h,('original changed externally',rel)
 if sha(K/rel)!=h:changes[rel]={'before':h,'after':sha(K/rel)}
for f in K.rglob('*'):
 if f.is_file() and not f.is_symlink():
  rel=str(f.relative_to(K))
  if rel not in base:changes[rel]={'before':None,'after':sha(f)}
staged={str(f.relative_to(R/'source/kernel')):sha(f) for f in (R/'source/kernel').rglob('*') if f.is_file()}
assert set(changes)==set(staged),(set(changes)-set(staged),set(staged)-set(changes))
assert all(changes[p]['after']==h for p,h in staged.items())
old=config(E/'physical-r5.config');new=config(R/'out/.config');delta={p:dict(before=old.get(p,'n'),after=new.get(p,'n')) for p in old.keys()|new.keys() if old.get(p,'n')!=new.get(p,'n')}
assert delta=={'CONFIG_CUSTOM_KERNEL_ACCELEROMETER':{'before':'n','after':'y'},'CONFIG_BMC156_ACC':{'before':'n','after':'y'},'CONFIG_MTK_BMA253':{'before':'y','after':'n'},'CONFIG_MTK_MC3416':{'before':'y','after':'n'}},delta
for option in ['CUSTOM_KERNEL_MAGNETOMETER','CUSTOM_KERNEL_ALSPS','CUSTOM_KERNEL_GYROSCOPE','CUSTOM_KERNEL_SENSORHUB','CUSTOM_KERNEL_ACCELGYRO','MTK_BMI160_I2C','MTK_ACCELHUB']:assert new.get('CONFIG_'+option,'n')=='n',option
runtime=json.loads((B/'integration-r5/runtime-source-preservation.json').read_text());protected={p:sha(K/p) for p in runtime['files']}
assert len(protected)==282 and all(protected[p]==v['expected'] for p,v in runtime['files'].items())
opts=json.loads((B/'evidence/runtime-config-baseline.json').read_text());assert len(opts)==58
assert all(new.get(p,'n')==v['physical'] for p,v in opts.items())
network=json.loads(Path('/srv/android/asus-network-runtime/handoff-r1/evidence/network-config-equivalence.json').read_text())['core']
assert all(new.get(p,'n')==v['physical'] for p,v in network.items())
first=json.loads(Path('/srv/android/asus-firstboot-runtime/evidence/firstboot-config-equivalence-r3.json').read_text())['options'];assert all(new.get(v['option'],'n')==v['expected'] for v in first)
assert sha(B/'build/.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f'
assert sha(B/'build/arch/arm64/boot/Image.gz-dtb')=='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401'
dt='arch/arm64/boot/dts/mediatek/asus-p00a.dts';assert sha(K/dt)==base[dt]
assert 'asus,allow-battery-charging' not in (K/dt).read_text()
for n in ['protocol-test.json','kernel-math-test.json','hal-callback-tests.json','registration-test.json','core-state-test.json']:
 assert json.loads((E/n).read_text())['exit']==0,n
assert all(x['exit']==0 for x in json.loads((E/'kernel-build.json').read_text()))
assert all(x['exit']==0 for x in json.loads((E/'hal-build.json').read_text()))
assert all(x['exit']==0 for x in json.loads((E/'policy-merge.json').read_text()))
# Check all strong undefined ELF symbols resolve in the exact frozen SDK37 libc.
def symbols(p,undefined=False):
 result=[]
 for line in subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True).splitlines():
  # Older readelf spells AArch64 IFUNC as the multi-token "<OS specific>: 10".
  m=re.match(r"\s*\d+:\s+[0-9a-fA-F]+\s+\d+\s+.+?\s+(GLOBAL|WEAK)\s+\S+\s+(\S+)\s+(\S+)",line)
  if m and ((m[2]=='UND')==undefined) and (not undefined or m[1]=='GLOBAL'):
   result.append(m[3].split('@')[0])
 return set(result)
so=R/'hal-out/sensors.mt8163.so';imports=symbols(so,True);provider=symbols(R/'sdk/lib/libc.so');assert imports<=provider,imports-provider
elf=subprocess.check_output(['readelf','-d',str(so)],text=True);assert '[libc.so]' in elf and elf.count('(NEEDED)')==1
# Static VINTF schema and init/policy checks, not a full-device compatibility claim.
cmd=[str(A/'out/host/linux-x86/bin/assemble_vintf'),'-i',str(R/'source/hal/manifest.xml'),'-o',str(E/'assembled-manifest.xml')]
p=subprocess.run(cmd,capture_output=True,text=True);(E/'vintf-schema.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n');assert p.returncode==0,p.stderr
shutil.copyfile(R/'out/.config',E/'resolved.config')
artifacts={}
for rel in ['drivers/misc/mediatek/sensors-1.0/accelerometer/bmc156_acc/bmc156_acc.o','drivers/misc/mediatek/sensors-1.0/accelerometer/accel.o','drivers/misc/mediatek/sensors-1.0/hwmon/sensor_attributes/sensor_attr.o','drivers/misc/mediatek/sensors-1.0/built-in.o']:
 p=R/'out'/rel;artifacts[rel]=dict(bytes=p.stat().st_size,sha256=sha(p))
shutil.copyfile(so,R/'source/hal/sensors.mt8163.so') if False else None
record=dict(status='SOURCE_OBJECT_MODEL_PROOF_ONLY',baseline_files_verified=len(base),base_physical_image_sha256=sha(B/'build/arch/arm64/boot/Image.gz-dtb'),base_config_sha256=sha(E/'physical-r5.config'),resolved_config_sha256=sha(E/'resolved.config'),source_changes=changes,config_delta=delta,protected_runtime_source_count=len(protected),protected_runtime_sources=protected,protected_runtime_config_count=len(opts),network_config_count=len(network),firstboot_config_count=len(first),board_dts_sha256=sha(K/dt),charging_opt_in_absent=True,original_physical_source_unchanged=True,full_image_built=False,device_operations=False,physical_hardware_tested=False,private_calibration_read=False,hal_sha256=sha(so),hal_imports_resolved=sorted(imports),objects=artifacts)
(E/'final-verification.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
with gzip.GzipFile(str(E/'baseline-source-hashes.json.gz'),'wb',mtime=0) as f:f.write((E/'baseline-source-hashes.json').read_bytes())
(E/'reference-source-pins.json').write_text(json.dumps({str(p.relative_to(R)):sha(p) for p in (R/'sdk/reference').rglob('*') if p.is_file()},indent=2)+'\n')
print('PASS baseline',len(base),'changed',len(changes),'runtime sources',len(protected),'config',len(opts),'+',len(network),'+',len(first),'HAL imports',len(imports))
print('CONFIG',sha(E/'resolved.config'),'HAL',sha(so))
