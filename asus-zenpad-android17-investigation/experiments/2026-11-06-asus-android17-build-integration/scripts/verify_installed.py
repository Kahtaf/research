#!/usr/bin/env python3
"""Inspect full-product staging after a successful real image build."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path('/srv/android/lineage24')
out=root/'out/target/product/p00a'
report=Path(sys.argv[1])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
g=json.loads(Path('/srv/android/asus-device-product/google-inline/evidence/inline-source-manifest.json').read_text())
results=[]
for rel,meta in g['payload_members'].items():
 p=out/rel
 actual=sha(p) if p.is_file() else None
 results.append(dict(path=rel,expected=meta['sha256'],actual=actual,match=actual==meta['sha256']))
graphics=[]
for source in sorted((root/'vendor/asus/p00a/proprietary').rglob('*.so')):
 rel=source.relative_to(root/'vendor/asus/p00a/proprietary')
 target=out/'system'/rel;vendor=out/'system/vendor'/rel
 assert sha(target)==sha(source),str(target)
 assert not vendor.exists() or vendor.is_symlink(), 'Stale vendor copy: '+str(vendor)
 if vendor.is_symlink():assert vendor.resolve()==target.resolve(),str(vendor)
 graphics.append(dict(path=str(target.relative_to(out)),sha256=sha(target)))
assert len(graphics)==34,len(graphics)
for arch in ['lib','lib64']:
 assert not (out/'system/vendor'/arch/'libp00a_legacy_memory.so').exists()
 assert (out/'system'/arch/'libp00a_legacy_memory.so').is_file()
required=['system/vendor/bin/hw/android.hardware.health-service.asus-p00a','system/framework/services.jar','system/bin/keystore2','system/system_ext/bin/hwservicemanager','system/vendor/bin/hw/android.hardware.keymaster@4.0-service','system/etc/init/hw/init.rc','ramdisk/fstab.mt8163']
installed=[dict(path=r,sha256=sha(out/r),bytes=(out/r).stat().st_size) for r in required]
cmd=[str(root/'out/host/linux-x86/bin/host_init_verifier')]
for name,rel in [('system','system'),('system_ext','system/system_ext'),('vendor','system/vendor'),('product','system/product')]:
 cmd.append('--out_'+name+'='+str(out/rel))
 passwd=out/rel/'etc/passwd'
 if passwd.exists():cmd+=['-p',str(passwd)]
 for contexts in (out/rel/'etc/selinux').glob('*property_contexts'):
  cmd.append('--property-contexts='+str(contexts))
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
props={};property_files=[]
for rel in ['system/build.prop','system/system_ext/build.prop','system/vendor/build.prop','system/product/build.prop','system/etc/prop.default','ramdisk/default.prop']:
 path=out/rel
 if not path.is_file():continue
 property_files.append(dict(path=rel,sha256=sha(path)))
 for line in path.read_text().splitlines():
  if line.startswith('#') or '=' not in line:continue
  k,v=line.split('=',1);props.setdefault(k.strip(),set()).add(v.strip())
for k,v in {'ro.adb.secure':'1','ro.debuggable':'1','ro.build.type':'userdebug','ro.build.version.sdk':'37','ro.product.first_api_level':'23'}.items():
 assert props.get(k)=={v},(k,props.get(k))
assert 'ro.vndk.version' not in props and 'ro.product.vndk.version' not in props
adb=out/'system/product/etc/security/adb_keys'
assert sha(adb)==sha(Path('/srv/android/asus-device-product/debug-adb-public-key'))
r=dict(google_payload=results,graphics=graphics,installed=installed,property_files=property_files,properties={k:sorted(v) for k,v in props.items()},authenticated_adb_public_key_sha256=sha(adb),host_init_verifier=dict(command=cmd,exit_code=p.returncode,output=p.stdout),hardware_tested=False,flash_ready=False)
report.write_text(json.dumps(r,indent=2)+'\n')
assert all(x['match'] for x in results),'Installed Google input differs; see report'
assert p.returncode==0,'Full installed init parser failed; see report'
print('All Google payload bytes match and full installed init parser passed.')
