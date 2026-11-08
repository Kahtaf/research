from pathlib import Path
import json,hashlib,base64,subprocess,os,resource
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');O=Path('/srv/android/asus-linux49-vintf-port-20261106')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((P/'evidence/frozen-before.json').read_text());results={}
for f,before in pins.items():results[f]={'before':before,'after':h(Path(f)),'unchanged':before==h(Path(f))}
for f,before in json.loads((P/'evidence/tools.json').read_text())['copied_tool_pins'].items():results[f]={'before':before,'after':h(Path(f)),'unchanged':before==h(Path(f))}
for old in (O/'baseline').rglob('*'):
 if old.is_file():
  new=P/'baseline'/old.relative_to(O/'baseline');results[str(new)]={'before':pins[str(old)],'after':h(new),'unchanged':pins[str(old)]==h(new)}
q=subprocess.run(['ldd',str(P/'tools/bin/assemble_vintf')],capture_output=True,text=True,timeout=10)
assert q.returncode==0 and '/srv/android/lineage24/out' not in q.stdout
files=[p for p in P.rglob('*') if p.is_file()];logical=sum(p.stat().st_size for p in files);allocated=sum(p.stat().st_blocks*512 for p in files)
r={'all_frozen_inputs_and_copied_tools_unchanged':all(x['unchanged'] for x in results.values()),'files':results,'owned_logical_bytes':logical,'owned_allocated_bytes':allocated,'max_bytes':256*1024*1024,'cpu_affinity':list(os.sched_getaffinity(0)),'address_space_limit':resource.getrlimit(resource.RLIMIT_AS),'copied_assembler_ldd':q.stdout,'current_metadata_read':False}
assert r['all_frozen_inputs_and_copied_tools_unchanged'] and max(logical,allocated)<r['max_bytes']
(P/'evidence/final-audit.json').write_text(json.dumps(r,indent=2))
exports={str(p.relative_to(P)):{'sha256':h(p),'base64':base64.b64encode(p.read_bytes()).decode()} for p in (P/'evidence').glob('*') if p.is_file() and p.suffix in ['.json','.log']}
print(json.dumps({'audit':r,'exports':exports},indent=2))
