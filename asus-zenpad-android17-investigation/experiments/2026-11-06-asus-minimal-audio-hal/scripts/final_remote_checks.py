from pathlib import Path
import os,resource,subprocess,json,hashlib,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out'
# Pin every compiler dependency actually used; no private paths or whole images.
pins={}
for dep in out.glob('*.d'):
 text=dep.read_text().replace('\\\n',' ');paths=text.split(':',1)[1].split()
 for path in paths:
  p=Path(path);p=p if p.is_absolute() else a/p
  if p.is_file():pins[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size}
for p in [a/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang',a/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/ld.lld']:
 pins[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size}
(out/'compile-input-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print('COMPILE_INPUT_PINS',len(pins))
for root in ['bionic','external/tinyalsa_new','hardware/libhardware','hardware/interfaces','system/media','system/sepolicy']:
 p=subprocess.run(['git','-C',str(a/root),'rev-parse','HEAD'],capture_output=True,text=True);print('GIT',root,p.returncode,p.stdout.strip())
llvm=a/'prebuilts/clang/host/linux-x86/clang-r584948b/bin';p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_hw_audio.primary.mt8163.so')
print('PUBLIC_PRIMARY_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
r=subprocess.run([llvm/'llvm-objdump','-d','--demangle',p],capture_output=True,text=True,check=True)
keep=[];on=False
for line in r.stdout.splitlines():
 if '>:' in line:on=bool(re.search('DC[Cc]|Dc[Cc]|DC_[Cc]|[Cc]alibration|[Cc]alibrate',line))
 if on:keep.append(line)
(out/'public-primary-dc.txt').write_text('\n'.join(keep)+'\n');print('PRIMARY_DC_LINES',len(keep))
# Actual available policy inputs, not an invented test policy.
for root in ['precompiled_sepolicy','sepolicy_neverallows','vendor_sepolicy.cil','plat_sepolicy.cil','plat_pub_versioned.cil','system_ext_sepolicy.cil','product_sepolicy.cil']:
 p=a/'out/soong/.intermediates/system/sepolicy'/root
 for f in p.rglob('*'):
  if f.is_file():print('POLICY',f,f.stat().st_size)
print('ANALYZER',(a/'out/host/linux-x86/bin/sepolicy-analyze').exists())

for rel in ['hardware/libhardware/hardware.c','device/asus/p00a/BoardConfig.mk']:
 p=a/rel
 print('LOADER_SOURCE',rel,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 for n,l in enumerate(p.read_text().splitlines(),1):
  if any(v in l for v in ['ro.hardware','ro.board.platform','ro.product.board','class_id','inst','TARGET_BOARD_PLATFORM']):print(n,l)
p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_libaudiocustparam.so');print('PUBLIC_AUDIOCUSTPARAM_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
