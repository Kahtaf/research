"""Load observer with subprocess replaced by an in-memory stub; NO ADB execution."""
import sys,importlib.util,json,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];p=R.parent/'2026-11-06-asus-android17-os-rescue/source/observer.py'
spec=importlib.util.spec_from_file_location('offline_observer',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pin={'stock_serial':m.STOCK,'usb':'TEST-PORT','stock_fingerprint':m.FINGERPRINT,'stock_device':'P00A_2','stock_product':'WW_P00A','stock_model':'P00A_2','captured_utc':'2000-01-01T00:00:00Z'}
res={'physical_commands':0,'inputs':'synthetic; subprocess entirely replaced','stale_pin_accepted':m.select([],pin) is None}
row={'serial':'P00A49PROBE','state':'recovery','usb':'TEST-PORT','transport_id':'45','product':'p00a_diagnostic','model':'P00A_RAM_diagnostic','device':'p00a'}
try:m.select([row],pin);res['new_probe']='accepted'
except m.Refused as e:res['new_probe']='refused: '+str(e)
bad=b'REPORT_ENDPOINT uid=2000 context=u:r:shell:s0\n'+m.MARKER+b'\nandroidboot.serialno='+m.STOCK.encode()+b'WRONG\n[ /sys/fs/selinux/enforce ]\n0\n[ /sys/class/power_supply/battery/uevent ]\nread errno=5\nEND_DIAGNOSTIC\n'
res['substring_checker_accepts_wrong_serial_enforcing_zero_and_read_error']=m.validate_report(bad,0)
out=R/'evidence/observer-simulation';pinpath=R/'evidence/synthetic-pin.json';pinpath.write_text(json.dumps(pin))
inventories=[f'List of devices attached\n{m.DIAGNOSTIC} recovery usb:TEST-PORT product:p00a_diagnostic model:P00A_RAM_diagnostic device:p00a transport_id:45\n',f'List of devices attached\n{m.STOCK} device usb:TEST-PORT product:WW_P00A model:P00A_2 device:P00A_2 transport_id:46\n']
commands=[]
def fake_run(argv,**kw):
 commands.append(argv);assert argv[0]=='adb'
 if argv[1:]==['devices','-l']:return types.SimpleNamespace(returncode=0,stdout=inventories.pop(0).encode())
 assert argv[1:3] in (['-t','45'],['-t','46'])
 if argv[3:]==['shell','report']:return types.SimpleNamespace(returncode=74,stdout=b'open errno=13\n')
 assert argv[3:5]==['shell','getprop'];return types.SimpleNamespace(returncode=0,stdout={'ro.serialno':m.STOCK,'ro.build.fingerprint':m.FINGERPRINT,'ro.build.version.sdk':'24','sys.boot_completed':'1'}[argv[5]].encode())
m.subprocess=types.SimpleNamespace(run=fake_run);m.time=types.SimpleNamespace(monotonic=lambda:0,time=lambda:0,time_ns=lambda:1,sleep=lambda _:None)
sys.argv=['offline-observer','--pin',str(pinpath),'--out',str(out),'--observe'];m.main()
last=json.loads((out/'events.jsonl').read_text().splitlines()[-1]);res.update(main_returned_normally=True,final_event=last,stubbed_commands=commands)
(R/'evidence/observer-faults.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({k:v for k,v in res.items() if k!='stubbed_commands'},indent=2))
