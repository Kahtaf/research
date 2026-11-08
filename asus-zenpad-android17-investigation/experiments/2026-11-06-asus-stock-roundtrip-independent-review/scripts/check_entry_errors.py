"""Actual entry adapter plus actual controller/engine; subprocess and device are fixtures."""
from pathlib import Path
import sys,importlib.util,json,datetime,subprocess
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];C=R.parent/'2026-11-06-asus-stock-roundtrip-continuation'
spec=importlib.util.spec_from_file_location('entry_error_fixture',C/'tests/service/test_faults.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m.S=R
(R/'tests').mkdir(exist_ok=True);results=[]
for name,rc,err in [('closed_transport',1,b'error: closed\n'),('adb_killed',-9,b'')]:
 case=m.Base();case.setUp();classification=[]
 def entry(host,pin):
  host.entries+=1;host.dev.step('host:entry')
  adapter=m.T.HostIO(case.root/'adapter-commands')
  with patch.object(adapter,'command',return_value=subprocess.CompletedProcess(['FIXTURE'],rc,b'',err)):
   delivery=adapter.entry(pin)
  classification.append(delivery);return delivery
 try:
  with patch.object(m.FakeHost,'entry',entry):d,h,r=case.trial()
  assert classification[0]['delivery']=='completion_unconfirmed'
  assert h.tcp==1 and d.writes==['candidate','stock']
  results.append(dict(case=name,adb_exit_code=rc,adb_stderr=err.decode(),delivery=classification[0],
   tcp_reenable_calls=h.tcp,writes=d.writes,outcome=r['outcome'],stock_returned=r['stock_returned']))
 finally:case.tearDown()
(R/'evidence/entry-error-boundaries.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 device_contacted=False,status='UNCERTAIN_ENTRY_CLASSIFICATION_GAP_REPRODUCED',cases=results),indent=2)+'\n')
print(json.dumps(results,indent=2))
