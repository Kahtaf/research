from pathlib import Path
import json,difflib,shutil,hashlib
R=Path(__file__).resolve().parents[1];E=R/'evidence';C=R/'candidate'
s=(E/'00-resolved-baseline.txt').read_text();b=json.loads(s[s.index('{\n'):]);d=json.loads((E/'01-explicit-target7.json').read_text())
for n,x in [('00-resolved-baseline',b),('01-explicit-target7',d)]:
 (E/(n+'.log')).write_text(x['log']);(E/(n+'-command.json')).write_text(json.dumps(x['receipt'],indent=2)+'\n')
old=R.parent/'2026-11-06-asus-root-property-and-independent-packaging/evidence/vm-r2/checks/checkvintf-command.json'
shutil.copy2(old,E/'original-checkvintf-command.json')
shutil.copy2(old.with_name('checkvintf.log'),E/'original-checkvintf.log')
a=json.loads(old.read_text());new={'argv':b['receipt']['argv'],'expected_exit_until_profile_supplied':65,'tool_sha256':a['tool_sha256'],'kernel_config_sha256':'10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2','status':'CORRECTED_TEST_INPUT_ONLY_NO_PRODUCT_PROFILE_APPROVED'}
(C/'checkvintf-command.json').write_text(json.dumps(new,indent=2)+'\n')
oldargs=json.dumps({'argv':a['argv']},indent=2)+'\n';newargs=json.dumps({'argv':new['argv']},indent=2)+'\n'
(C/'checkvintf-inputs.patch').write_text(''.join(difflib.unified_diff(oldargs.splitlines(True),newargs.splitlines(True),fromfile='a/checkvintf-command.json',tofile='b/checkvintf-command.json')))
pre=R/'source/device/asus/p00a/manifest.xml';post=pre.read_text().replace('type="device"','type="device" target-level="7"',1)
(C/'REJECTED-target7-diagnostic.patch').write_text(''.join(difflib.unified_diff(pre.read_text().splitlines(True),post.splitlines(True),fromfile='a/device/asus/p00a/manifest.xml',tofile='b/device/asus/p00a/manifest.xml')))
# Only source files actually read, with observed remote hashes, plus exact installed metadata.
pins=b['receipt']['pins'].copy()
for p in E.glob('*.json'):
 if p.name not in ['source-files.json','more-sources.json','metadata-sources.json','first-api-sources.json','semantic-source-detail.json','build-rules.json']:continue
 for f,x in json.loads(p.read_text()).items():
  if isinstance(x,dict) and 'base64' in x and not f.startswith('metadata/'):
   pins['/srv/android/lineage24/'+f]={'sha256':x['sha256'],'bytes':len(__import__('base64').b64decode(x['base64']))}
for f,sha in [('/srv/android/asus-bmc156-full-kernel-r1/export-compact/artifacts/resolved.config','10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2')]:pins[f]={'sha256':sha}
(E/'all-before-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
script='''from pathlib import Path
import json,hashlib
P=Path('/srv/android/asus-linux49-vintf-port-20261106')
pins='''+repr(pins)+'''
r={}
for f,pin in pins.items():
 p=Path(f);after=hashlib.sha256(p.read_bytes()).hexdigest();r[f]={'before_sha256':pin['sha256'],'after_sha256':after,'unchanged':after==pin['sha256']}
files=[p for p in P.rglob('*') if p.is_file()]
bytes_total=sum(p.stat().st_size for p in files);allocated=sum(p.stat().st_blocks*512 for p in files)
result={'all_unchanged':all(x['unchanged'] for x in r.values()),'files':r,'owned_file_bytes':bytes_total,'owned_file_allocated_bytes':allocated,'owned_regular_file_count':len(files),'max_bytes':256*1024*1024}
assert bytes_total < 256*1024*1024 and allocated <256*1024*1024
(P/'checks/final-prepost.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
'''
(R/'scripts/final_verify.py').write_text(script)
print('Staged corrected command, input patch, rejected diagnostic patch, and source/metadata audit.')
