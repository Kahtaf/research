"""Fixed SSH helper; this script only stages/builds/fetches this owned prefix."""
from pathlib import Path
import importlib.util,base64,json,sys
R=Path(__file__).resolve().parents[1];W=R.parent
s=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
P='/srv/android/asus-retained-report-control-20261107'
if sys.argv[1]=='compile':
 payload={rel:base64.b64encode((R/rel).read_bytes()).decode() for rel in ['source/init.c','scripts/compile_helper.py']}
 print(m.run(f'''from pathlib import Path
import base64,subprocess
R=Path({P!r})
for p,data in {payload!r}.items():(R/p).write_bytes(base64.b64decode(data))
p=subprocess.run(['python3','-B',str(R/'scripts/compile_helper.py')],capture_output=True,text=True,timeout=150)
print(p.stdout);print(p.stderr);assert p.returncode==0
'''))
elif sys.argv[1]=='fetch':
 rels=['artifacts/init','evidence/helper-compile.json','source/kernel-reference/mm/early_ioremap.c','source/kernel-reference/arch/arm64/include/asm/fixmap.h','source/kernel-reference/include/asm-generic/early_ioremap.h']
 out=json.loads(m.run(f'''from pathlib import Path
import base64,json
R=Path({P!r});print(json.dumps({{p:base64.b64encode((R/p).read_bytes()).decode() for p in {rels!r}}}))'''))
 for rel,data in out.items():
  p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
else:raise SystemExit('compile or fetch')
