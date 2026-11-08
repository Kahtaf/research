exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
script=r'''
from pathlib import Path
import json,hashlib,gzip,re
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r7')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
rels=['device/asus/p00a/connectivity/src/driver_cmd_p00a.c','device/asus/p00a/connectivity/Android.bp','device/asus/p00a/sepolicy/vendor/file_contexts','build/soong/ui/build/config.go','build/soong/ui/build/ninja.go','build/soong/ui/status/log.go','build/soong/ui/logger/logger.go']
files={r:(A/r).read_text() for r in rels if (A/r).is_file()}
needles=['system/bpf/loader/bpfloader/','system/vold/libvold/','device/asus/p00a/sensors/sensors.mt8163/','system/vold/vold/','bpf/loader/bpfloader.rs','bpf/','netd.o']
lines=[]
with gzip.open(A/'out/verbose.log.gz','rt',errors='replace') as f:
 for n,l in enumerate(f,1):
  if any(x in l for x in needles) and any(x in l for x in ['clang','rustc','ld.lld']):lines.append(dict(line=n,text=l.rstrip()))
policy={str(p.relative_to(A)):dict(sha256=sha(p),bytes=p.stat().st_size) for base in ['out/target/product/p00a/obj/ETC','out/host/linux-x86/bin'] for p in (A/base).glob('**/*') if p.is_file() and any(x in p.name for x in ['file_contexts','sepolicy','secilc','checkfc','sefcontext','selabel'])}
print(json.dumps(dict(files=files,files_sha256={r:sha(A/r) for r in files},commands=lines,policy=policy,r7_integration=json.loads((R/'attempt/integration.json').read_text()),r7_plan=json.loads((R/'inputs/plan.json').read_text())),indent=2))
'''
r=m.run(script);Path('2026-11-06-asus-r8-continuation-kit/evidence/remote-inputs.json').write_text(r);d=json.loads(r)
for rel,content in d['files'].items():
 out=Path('2026-11-06-asus-r8-continuation-kit/inputs/public-source')/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(content)
print(json.dumps(dict(files=d['files_sha256'],commands_count=len(d['commands']),command_slices=[{'line':x['line'],'text':x['text'][:280]} for x in d['commands'][:12]],policy=d['policy']),indent=2))
