"""Conservative publication selection from the sanitized local checkpoint.
Read-only source; no upstream postimages. Run from archive parent with python3
selection.py --checkpoint /PATH/TO/local-checkpoint --output /PATH/TO/fresh-publication. This script itself is authored for this export.
"""
from pathlib import Path
import argparse,collections,hashlib,json,re,shutil
parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();src=args.checkpoint.resolve();dst=args.output.resolve();dst.mkdir(parents=True,exist_ok=False)
rows=[];reasons=collections.Counter();sources={}
for mp in [src/'manifest.json',src/'remote/manifest.json',src/'source-checkpoints/manifest.json']:
 for x in json.loads(mp.read_text()):sources[x['path']]=x
third=re.compile(r'copyright[^\n]*(?:mediatek|arm limited|arm ltd|google|linaro|free software foundation|the android open source|intel|qualcomm|nvidia)',re.I)
config={'.mk','.bp','.rc','.te','.cil','.xml','.conf','.config','.defconfig','.dts','.dtsi','.toml','.yaml','.yml'}
for rel,x in sorted(sources.items()):
 p=Path(rel);f=src/p;parts=p.parts;ext=p.suffix;reason='';keep=False;text=f.read_text()
 if ext in {'.patch','.diff'}:keep=True;reason='authored Git/source delta, no full fetched tree'
 elif parts[0]=='source-checkpoints':
  if 'authored-java' in parts and p.name=='MainActivity.java':keep=True;reason='new project Wi-Fi setup helper Java'
  else:reason='fetched/modified existing source postimage or checkpoint; retain delta/provenance instead'
 elif parts[0]=='remote':
  if parts[1] in {'provenance','build-entrypoints'} or p.name=='platform-project-state.json':keep=True;reason='source pins/project states or authored root build entrypoint'
  elif parts[1]=='platform-untracked-source' and p.name in {'namespace_ownership_test.cc','p00a_legacy_graphics_test.cc'}:keep=True;reason='new untracked linkerconfig tests established by VM source audit'
  elif parts[1]=='active-device-source' and ext in config and 'rootdir' not in parts:keep=True;reason='project device/vendor configuration'
  elif parts[1]=='reviewed-kit-r9-exec-r1' and parts[2] in {'scripts','tests'} and ext in {'.py','.sh'} and not third.search(text):keep=True;reason='authored kit script/test'
  elif ext=='.json' and parts[1]=='reviewed-kit-r9-exec-r1':keep=True;reason='compact kit evidence/provenance metadata'
  else:reason='remote fetched/modified source postimage or duplicate kit snapshot; retain patches/provenance'
 elif parts[0]=='experiments':
  area=parts[2] if len(parts)>3 else ''
  if any(v in {'original','baseline','tmp','candidates','replay','z380m-alpine'} for v in parts[2:]):reason='duplicate/baseline/fetched snapshot, retain canonical authored files and reports'
  elif ext=='.md':keep=True;reason='investigation report/readme/handoff'
  elif ext=='.json':keep=True;reason='selected result/source-pin/hash metadata'
  elif ext in {'.py','.sh','.bash'} and not third.search(text):keep=True;reason='authored investigation/build/packaging helper'
  elif (ext in config or p.name in {'file_contexts','property_contexts','fs_config','Makefile','Dockerfile','series'}) and area not in {'source','sources'} and not third.search(text):keep=True;reason='authored experiment configuration'
  elif ext in {'.c','.h','.S','.s'} and len(parts)==4 and area in {'source','scripts'} and re.search(r'(?:rescue|frontend|fault_collection|asus_entry|patcher|ram_|ramprobe|probe_init|serial_probe|delay_probe)',p.name) and not re.search(r'(?:before|after|original|stock|kernel)',p.name) and not third.search(text):keep=True;reason='clearly named new standalone RAM/rescue/probe helper'
  else:reason='uncertain authorship or full existing source/config postimage; conservative exclusion'
 if keep:
  target=dst/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);target.chmod(0o644)
  assert hashlib.sha256(target.read_bytes()).hexdigest()==x['export_sha256']
 row=dict(x);row.update(selected=keep,filter_reason=reason,local_checkpoint_path=rel,publication_path=rel if keep else None);rows.append(row);reasons[('included: ' if keep else 'excluded: ')+reason]+=1
selected=[x for x in rows if x['selected']]
(dst/'publication-mapping.json').write_text(json.dumps(rows,indent=2)+'\n')
(dst/'manifest.json').write_text(json.dumps(selected,indent=2)+'\n')
for name in ['experiment-index.json','EXPERIMENT-LEDGER.md','STATE-AND-RESUME.md','known-image-identities.json','SOURCE-PRESERVATION.json','source-checkpoints/source-bundles.json']:
 p=src/name
 if p.exists():q=dst/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
summary={'indexed_experiments':391,'included_files':len(selected),'included_bytes':sum(x['export_bytes'] for x in selected),'excluded_files':len(rows)-len(selected),'selection_counts':dict(reasons),'note':'391 experiment boundaries retained. Omitted fetched or uncertain source remains in local checkpoint only. Relative paths retained, but links to omitted postimages may not resolve; publication-mapping.json explains every omission. No license is asserted for preserved patches.'}
(dst/'publication-selection.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
