import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,sys,subprocess,re
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');sys.path.insert(0,str(R/'scripts'))
from integrate import sha
r=json.loads((R/'evidence/cache-gap.json').read_text());rows=[]
for x in r['first']:
 p=A/x['output']
 if not p.is_file():rows.append(dict(output=x['output'],missing=True));continue
 row=dict(output=x['output'],sha256=sha(p),bytes=p.stat().st_size,ninja=x['entry'])
 if '/unstripped/' in str(p):
  result=subprocess.run([str(A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readelf'),'-n',str(p)],capture_output=True,text=True,timeout=20)
  assert result.returncode==0;row['build_id']=re.findall(r'Build ID:\s*([0-9a-f]+)',result.stdout)
  rel='system/bin/'+p.name;installed=A/'out/target/product/p00a'/rel
  row['installed_pin']=dict(path=rel,sha256=sha(installed),bytes=installed.stat().st_size)
  result=subprocess.run([str(A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readelf'),'-n',str(installed)],capture_output=True,text=True,timeout=20)
  assert result.returncode==0;row['installed_build_id']=re.findall(r'Build ID:\s*([0-9a-f]+)',result.stdout)
  assert row['build_id']==row['installed_build_id']
 rows.append(row)
output=dict(first_phase_selected_outputs=rows,first_phase_receipt_sha256=sha(Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/host_init_verifier/receipt.json')),source_pins={s:sha(A/s) for s in ['system/bpf/loader/bpfloader.rs','system/vold/model/PublicVolume.cpp']},current_observation_only=True,execution_time_dependency_identity_proven=False,current_ninja_entries_for_these_outputs=r['current'])
with (R/'evidence/cache-current-identity.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
print(json.dumps(output,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/cache-current-identity.json').write_text(r);print('Preserved current identity evidence for genuine r8 first-phase outputs; no cached admission claimed.')
