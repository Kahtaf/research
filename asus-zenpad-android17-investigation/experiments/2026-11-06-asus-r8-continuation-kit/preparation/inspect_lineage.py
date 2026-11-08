exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
script=r'''
from pathlib import Path
import json,gzip,hashlib
A=Path('/srv/android/lineage24')
mods=['system/bpf/loader/bpfloader/','system/vold/libvold/','system/vold/vold/','device/asus/p00a/sensors/sensors.mt8163/']
rows=[]
with (A/'out/.ninja_log').open() as f:
 for l in f:
  if any(x in l for x in mods):
   parts=l.rstrip().split('\t');p=A/parts[3];rows.append(dict(line=l.rstrip(),exists=p.is_file(),stat=p.stat().st_mtime_ns if p.is_file() else None,depfile=Path(str(p)+'.d').is_file()))
print(json.dumps(dict(ninja=rows,verbose_context=[(n,l.rstrip()) for n,l in enumerate(gzip.open(A/'out/verbose.log.gz','rt',errors='replace'),1) if n in range(7817,7822) or n in range(8820,8830)],siso_files=[str(p) for p in A.glob('out/*') if any(x in p.name for x in ['siso','ninja','deps'])],policyfiles=[str(p) for p in A.glob('out/soong/.intermediates/system/sepolicy/**/sepolicy')][:20]),indent=2))
'''
r=m.run(script);Path('2026-11-06-asus-r8-continuation-kit/evidence/lineage-inspect.json').write_text(r);d=json.loads(r);print(json.dumps(dict(ninja=d['ninja'][-20:],siso_files=d['siso_files'],policyfiles=d['policyfiles'],verbose_context=[(n,t[:350]) for n,t in d['verbose_context']]),indent=2))
