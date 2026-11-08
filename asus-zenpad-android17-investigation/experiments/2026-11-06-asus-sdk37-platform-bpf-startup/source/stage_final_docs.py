from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('builder_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
files={n:(ROOT/n).read_text() for n in ['report.md','PARENT-KIT-DELTA.md','parent-kit-delta.json']}
script=f'''from pathlib import Path
import json
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');D=O/'inputs/handoff-docs';D.mkdir(exist_ok=False)
for name,text in {files!r}.items():(D/name).write_text(text)
q=json.loads((O/'evidence/qualification.json').read_text());selection=json.loads((O/'evidence/selection-v2.json').read_text());q['missing_selected_outputs']=[x for x in selection['objects'] if x.get('missing')];q['authoritative_selection']='evidence/selection-v2.json';q['selection_reaudit']='evidence/selection-v2-audit.json'
(O/'evidence/qualification-v2.json').write_text(json.dumps(q,indent=2)+'\\n');print('Staged final documents and refined qualification receipt')
'''
print(m.run(script))
