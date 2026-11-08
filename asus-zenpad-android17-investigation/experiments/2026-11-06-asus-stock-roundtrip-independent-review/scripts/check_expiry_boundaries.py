"""Review-only reproductions; actual controller/engine, typed host/storage fixtures."""
from pathlib import Path
import sys,importlib.util,json,datetime
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];C=R.parent/'2026-11-06-asus-stock-roundtrip-continuation'
spec=importlib.util.spec_from_file_location('expiry_fixture',C/'tests/service/test_faults.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m.S=R
(R/'tests').mkdir(exist_ok=True)
results=[]
for name,boundary,fault in [('candidate_after_expiry','install:stage_candidate',None),
 ('internal_inverse_after_expiry','install:write_candidate','install:write_candidate'),
 ('explicit_inverse_after_expiry','restore:stage_stock',None)]:
 case=m.Base();case.setUp();expired=[False];checks=[];writes=[];real_step=m.Device.step;real_write=m.MemoryTransport.write
 def step(dev,label):
  if label==boundary:expired[0]=True
  return real_step(dev,label)
 def write(t,kind):
  writes.append({'phase':t.phase,'kind':kind,'review_expired':expired[0]})
  return real_write(t,kind)
 def check():
  checks.append({'expired':expired[0]})
  if expired[0]:raise m.F.Refused('REVIEW FIXTURE expired')
 try:
  with patch.object(m.Device,'step',step),patch.object(m.MemoryTransport,'write',write):
   d,h,r=case.trial(fault=fault,kind='failed' if fault else 'uncertain',recheck=check)
  assert any(x['review_expired'] for x in writes)
  results.append(dict(case=name,expiry_boundary=boundary,review_checks=checks,writes=writes,
   outcome=r['outcome'],p10_restored=r['p10_restored'],entry_requests=r['entry_requests'],calls=d.calls))
 finally:case.tearDown()
(R/'evidence/expiry-boundaries.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 device_contacted=False,status='GAP_REPRODUCED',cases=results),indent=2)+'\n')
print(json.dumps([dict(case=x['case'],writes=x['writes'],outcome=x['outcome']) for x in results],indent=2))
