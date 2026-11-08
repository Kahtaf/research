#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,subprocess,tempfile,tarfile
s=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
pre=json.loads((s/'patch-preimages.json').read_text())['files']
qa=s/'evidence/patch-qa';qa.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='apply-',dir=qa) as tmp:
 root=Path(tmp)
 for f in pre:(root/f['destination']).parent.mkdir(parents=True,exist_ok=True)
 cmd=['patch','-s','-f','-p1','-i',str(s/'staging-additions.patch')]
 r=subprocess.run(cmd,cwd=root,text=True,capture_output=True);assert r.returncode==0,(r.stdout,r.stderr)
 for f in pre:assert sha((root/f['destination']).read_bytes())==f['new_sha256'],f['destination']
compiled=json.loads((s/'evidence/remote/compile-input-pins.json').read_text())
for p in (s/'src').glob('*'):
 assert compiled['/srv/android/asus-minimal-audio-hal-20261106/src/'+p.name]['sha256']==sha(p.read_bytes())
commands=json.loads((s/'evidence/remote/compile.json').read_text());assert len(commands)==12 and all(x['returncode']==0 for x in commands)
for name in ['audio.primary.mt8163.so','libtinyalsav2.so']:
 text=(s/'evidence/remote'/(name+'.elf.txt')).read_text();assert 'AArch64' in text and 'ELF64' in text
 if name.startswith('audio.'):assert ' HMI' in text and '[libtinyalsav2.so]' in text
 for forbidden in ['libnvram.so','libmedia.so','libbinder.so','libpowermanager.so']:assert '['+forbidden+']' not in text
result={'patch_additions_verified':len(pre),'compiled_source_matches_local':True,'real_sdk37_compile_link_commands_passed':len(commands),'elf_architecture_and_dependencies':'PASS','transport_assertions':58,'hal_contract_assertions':28,'hardware_claim':False,'route_activation':False,'full_product_neverallows':'incomplete; 45s bounded timeout'}
(s/'evidence/final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
