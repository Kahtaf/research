from pathlib import Path
import json,hashlib,subprocess,time,os,resource
P=Path('/srv/android/asus-linux49-vintf-port-20261106');S=Path('/srv/android/lineage24')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={};copies=[]
prod=S/'out/target/product/p00a/system'
for part,src in [('system',prod),('vendor',prod/'vendor'),('product',prod/'product'),('system_ext',prod/'system_ext'),('odm',prod/'vendor/odm')]:
 for f in (P/'baseline'/part).rglob('*'):
  if f.is_file():
   original=src/f.relative_to(P/'baseline'/part);assert h(f)==h(original);pins[str(original)]={'sha256':h(original),'bytes':original.stat().st_size}
A=Path('/srv/android/asus-r9-postbuild-validation-r2/validation/apex')
for f in (P/'baseline/apex').rglob('*'):
 if f.is_file():
  original=A/f.relative_to(P/'baseline/apex');assert h(f)==h(original);pins[str(original)]={'sha256':h(original),'bytes':original.stat().st_size}
for f in ['inputs/kernel.release','inputs/resolved.config']:
 print(f,(P/f).read_text()[:150])
tool=S/'out/host/linux-x86/bin/checkvintf'
pins[str(tool)]={'sha256':h(tool),'bytes':tool.stat().st_size}
assert h(tool)=='f67a37ca56cc1fbb8cf5c919a69990e8493ab0a17248a9cd053ff97d7d1ba4c0'
for f in ['device/asus/p00a/BoardConfig.mk','device/asus/p00a/manifest.xml','system/libvintf/VintfObject.cpp','system/libvintf/KernelInfo.cpp','system/libvintf/AssembleVintf.cpp','system/libvintf/check_vintf.cpp','system/libvintf/RuntimeInfo.cpp','system/libvintf/CompatibilityMatrix.cpp','hardware/interfaces/compatibility_matrices/build/vintf_compatibility_matrix.go','kernel/configs/build/kernel_config.go']:
 p=S/f;pins[str(p)]={'sha256':h(p),'bytes':p.stat().st_size}
(P/'inputs/before-pins.json').write_text(json.dumps(pins,indent=2))
argv=[str(tool),'--check-compat']
for part in ['system','vendor','product','system_ext','odm','apex']:argv+=['--dirmap',f'/{part}:{P}/baseline/{part}']
argv+=['--kernel',f'{P}/inputs/kernel.release:{P}/inputs/resolved.config']
for prop in ['ro.product.first_api_level=23','ro.boot.product.hardware.sku=','ro.boot.product.vendor.sku=']:argv+=['--property',prop]
t=time.monotonic();r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
(P/'checks').mkdir();(P/'checks/00-resolved-baseline.log').write_text(r.stdout+r.stderr)
receipt={'argv':argv,'exit':r.returncode,'seconds':time.monotonic()-t,'log_sha256':h(P/'checks/00-resolved-baseline.log'),'copied_files':copies,'owned_bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),'limits':{'cpus':list(os.sched_getaffinity(0)),'address_space':resource.getrlimit(resource.RLIMIT_AS),'command_timeout_seconds':30},'pins':pins}
(P/'checks/00-resolved-baseline.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'receipt':receipt,'log':r.stdout+r.stderr},indent=2))
