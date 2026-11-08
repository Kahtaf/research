from pathlib import Path
import sys,json,base64
sys.path.insert(0,str(Path(__file__).resolve().parent));from remote_owned import run
L=Path(__file__).resolve().parents[1]
script='''from pathlib import Path
import json,base64
R=Path('/srv/android/asus-android-runtime-network-parity-20261107')
names=['run-runtime/serial.log','run-runtime/command.json','run-runtime/started.json','run-runtime/status.json','run-patch/status.json','run-patch/serial.log']
names += ['evidence/'+n for n in ['admission.json','adaptations.json','prepare-commands.json','cow-verification.json','boot-ramdisk-corroboration.json','selected-init-source-pins.json','final-aconfigd.rc','final-odsign.rc','final-init.mt8163.rc','report-extraction.json','public-report-compact.txt','serial-highlights.txt','base-unchanged-receipt.json']]
names += ['evidence/'+n for n in ['integration.json','patch-application.json','build-started.json','build-result.json','build.log','build-runner.log','startup-pipeline-result.json','original.config','built.config']]
result={}
for n in names:
 p=R/n
 if p.is_file():
  assert p.stat().st_size<8*1024**2
  result[n]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(result))
'''
result=json.loads(run(script))
for name,value in result.items():
 p=L/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(base64.b64decode(value))
print(json.dumps({n:(L/n).stat().st_size for n in result},indent=2))
