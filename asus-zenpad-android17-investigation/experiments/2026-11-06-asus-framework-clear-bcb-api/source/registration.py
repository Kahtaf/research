from pathlib import Path
import json
from dex import Dex
from disasm_dex import decode,listing
S=Path(__file__).resolve().parents[1];d=Dex(S/'inputs/framework__oat__arm64__services.odex.dex1');out=[]
c=d.classdata('Lcom/android/server/SystemServer;')
for m in c['methods']:
 if '->startOtherServices(' not in m['name']:continue
 code=d.code(m['code_offset']);rows=decode(d,code)
 for i,r in enumerate(rows):
  if r.get('ref')=='Lcom/android/server/RecoverySystemService;':
   window=rows[max(0,i-4):i+7];out.append(dict(method=m['name'],code_offset=m['code_offset'],instructions=window));(S/'evidence/SystemServer-recovery-registration.txt').write_text(listing(m['name'],code,window))
assert len(out)==1
c=d.classdata('Lcom/android/server/SystemService;')
for m in c['methods']:
 if '->publishBinderService(' not in m['name']:continue
 code=d.code(m['code_offset']);rows=decode(d,code);out.append(dict(method=m['name'],code_offset=m['code_offset'],instructions=rows))
(S/'evidence/registration.json').write_text(json.dumps(out,indent=2)+'\n');print((S/'evidence/SystemServer-recovery-registration.txt').read_text())
