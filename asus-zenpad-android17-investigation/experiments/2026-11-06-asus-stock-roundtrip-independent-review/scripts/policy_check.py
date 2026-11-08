from pathlib import Path
import json,hashlib,subprocess,sys,datetime
R=Path(__file__).resolve().parents[1];W=R.parent;P=W/'2026-11-06-asus-stock-programmatic-control'
audit=json.loads((P/'evidence/service/firmware-audit.json').read_text())
tool=W/'2026-11-06-asus-android17-os-rescue/artifacts/tools-final/policy_constraints'
assert hashlib.sha256(tool.read_bytes()).hexdigest()==audit['policy_tool_sha256']
assert hashlib.sha256((P/'artifacts/stock-boot.sepolicy').read_bytes()).hexdigest()=='873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f'
def isolate(event,args):
 if event.startswith('socket.') or event in ('os.system','os.exec','os.posix_spawn'):raise RuntimeError('Offline only')
 if event=='subprocess.Popen' and Path(args[0]).resolve()!=tool:raise RuntimeError('Only saved local policy evaluator permitted')
sys.addaudithook(isolate)
checks=[]
for old in audit['policy_checks']:
 assert old['argv'][0]==str(tool) and old['argv'][1]==str(P/'artifacts/stock-boot.sepolicy')
 result=subprocess.run(old['argv'],capture_output=True,text=True,timeout=10,check=True)
 assert result.stdout==old['stdout']
 checks.append(dict(argv=old['argv'],stdout=result.stdout))
(R/'evidence/policy-replay.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',
 device_contacted=False,checks=checks,limits='Saved stock policy; no current loaded-policy observation.'),indent=2)+'\n')
print('PASS: three saved-stock policy access checks; no device contact')
