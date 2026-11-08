from pathlib import Path
import json,hashlib,shutil,subprocess,re,datetime,os
R=Path('/srv/android/asus-genuine-service-runtime');T=Path('/srv/android/lineage24');P=T/'out/target/product/p00a'
R.mkdir();(R/'evidence').mkdir();(R/'source').mkdir();(R/'tmp').mkdir();I=R/'inputs/capture-r1';I.mkdir(parents=True)
rows=[];missing=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(p):
 d=I/p.relative_to(T);d.parent.mkdir(parents=True,exist_ok=True)
 if d.exists():return
 a=sha(p);shutil.copy2(p,d);b=sha(p);c=sha(d);assert a==b==c,str(p)
 rows.append(dict(source=str(p),destination=str(d.relative_to(I)),bytes=p.stat().st_size,before=a,after=b,copy=c))
# Only selected runtime inputs, no whole partition images or private keys.
roots=['system/bin/apexd','system/system_ext/bin/hwservicemanager','system/bin/keystore2','system/bin/servicemanager','system/vendor/bin/hw/android.hardware.keymaster@4.0-service','system/bin/init','system/bin/linker64','system/bin/linkerconfig','system/bin/toybox','system/bin/sh','apex/com.android.adbd/bin/adbd']
libs=list((P/'system').glob('**/lib64/*.so'))+list((P/'apex').glob('*/lib64/*.so'))
queue=[P/p for p in roots];seen=set();deps=[]
while queue:
 p=queue.pop(0)
 if p in seen:continue
 seen.add(p)
 if not p.is_file():missing.append(str(p));continue
 freeze(p)
 out=subprocess.run(['readelf','-d',str(p)],capture_output=True,text=True)
 for n in re.findall(r'\(NEEDED\).*\[(.*?)\]',out.stdout):
  matches=[x for x in libs if x.name==n]
  deps.append(dict(consumer=str(p),needed=n,candidates=[str(x) for x in matches]))
  if not matches:missing.append(str(p)+':NEEDED:'+n)
  queue.extend(matches)
# Small metadata trees selected for init/linker/VINTF/SELinux/trust; no credentials.
for part in ['system','system/vendor','system/system_ext','system/product']:
 for sub in ['etc/init','etc/selinux','etc/vintf','etc/linkerconfig']:
  for p in (P/part/sub).rglob('*'):
   if p.is_file():freeze(p)
 for n in ['build.prop','etc/security/apexkeys.txt','etc/selinux/plat_sepolicy.cil','etc/ld.config.txt']:
  p=P/part/n
  if p.is_file():freeze(p)
  else:missing.append(str(p))
for p in (P/'system/apex').glob('*'):
 if p.is_file():freeze(p)
# Relevant generated metadata alternatives and source required for honest provenance.
for pat in ['build/soong/*-build.prop/android_common/build.prop','system/apex/apexd/apexkeys.txt/**/apexkeys.txt','system/sepolicy/**/*sepolicy.cil','system/sepolicy/**/precompiled_sepolicy','system/sepolicy/**/*contexts','system/sepolicy/**/202704.cil']:
 for p in (T/'out/soong/.intermediates').glob(pat):
  if p.is_file():freeze(p)
for base in ['system/core/rootdir','system/apex/apexd','system/security/keystore2/src','system/hwservicemanager','frameworks/native/cmds/servicemanager','hardware/interfaces/keymaster/4.0/default','device/asus/p00a']:
 for p in (T/base).rglob('*'):
  if p.is_file() and p.suffix in ['.rc','.rs','.cpp','.h','.xml','.prop','.mk','.bp','.cil','.te'] and '.git' not in p.parts:freeze(p)
# Check all sources again only after the complete selected snapshot.
changed=[x['source'] for x in rows if sha(Path(x['source']))!=x['before']]
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,changed=changed,missing=missing,dependencies=deps)
(R/'evidence/capture-r1.json').write_text(json.dumps(receipt,indent=2));assert not changed,changed
print(json.dumps(dict(files=len(rows),bytes=sum(x['bytes'] for x in rows),missing=missing,changed=changed),indent=2))
