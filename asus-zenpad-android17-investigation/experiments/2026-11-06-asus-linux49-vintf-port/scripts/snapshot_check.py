from pathlib import Path
import json,hashlib,shutil,subprocess,os,resource,time,base64
P=Path('/srv/android/asus-linux49-vintf-port-20261106');S=Path('/srv/android/lineage24')
assert not P.exists(), 'owned prefix must be new'
P.mkdir()
resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={}; copies=[]
def copy(src,dst):
 assert src.is_file() and src.stat().st_size < 8*1024*1024
 data=src.read_bytes();pins[str(src)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);copies.append(str(dst.relative_to(P)))
prod=S/'out/target/product/p00a/system'
for part,src in [('system',prod),('vendor',prod/'vendor'),('product',prod/'product'),('system_ext',prod/'system_ext'),('odm',prod/'vendor/odm')]:
 for sub in ['etc/vintf','etc/manifest.xml','etc/compatibility_matrix.xml']:
  root=src/sub
  if root.is_dir():
   for f in sorted(root.rglob('*')):
    if f.is_file():copy(f,P/'baseline'/part/f.relative_to(src))
  elif root.is_file():copy(root,P/'baseline'/part/sub)
A=Path('/srv/android/asus-r9-postbuild-validation-r2/validation/apex')
copy(A/'apex-info-list.xml',P/'baseline/apex/apex-info-list.xml')
for package in sorted(A.iterdir()):
 if package.is_dir():
  for f in sorted((package/'etc/vintf').rglob('*')):
   if f.is_file():copy(f,P/'baseline/apex'/f.relative_to(A))
config=Path('/srv/android/asus-bmc156-full-kernel-r1/export-compact/artifacts/resolved.config')
assert h(config)=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
copy(config,P/'inputs/resolved.config')
release=Path('/srv/android/asus-product-integration-staging/r3/kernel-source/kernel.release')
copy(release,P/'inputs/kernel.release');assert release.read_text().strip()=='4.9.337'
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
