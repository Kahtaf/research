import importlib.util,json
from pathlib import Path
p=Path('2026-11-06-asus-product-input-build-kit/scripts/remote.py')
s=importlib.util.spec_from_file_location('remote',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
script=r'''
from pathlib import Path
import json,hashlib,gzip
A=Path('/srv/android/lineage24')
def item(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
f=A/'out/siso_failed_commands.sh'
print(json.dumps({'failed_commands':f.read_text(),'failed_pin':item(f),'verbose_files':{str(p):item(p) for p in A.glob('out/verbose*')},'r7_attempt':{str(p):item(p) for p in Path('/srv/android/asus-reviewed-build-kit/r7/attempt').rglob('*') if p.is_file()},'mechanism':{rel:(A/rel).read_text() for rel in ['build/soong/ui/build/ninja.go']},'config_lines':[l for l in (A/'build/soong/ui/build/config.go').read_text().splitlines() if any(s in l for s in ['showcommands','verbose','NINJA_ARGS'])]},indent=2))
'''
result=m.run(script)
Path('2026-11-06-asus-r8-continuation-kit/evidence/remote-initial.json').write_text(result)
d=json.loads(result)
print(json.dumps({k:v for k,v in d.items() if k not in ['r7_attempt','mechanism']},indent=2))
