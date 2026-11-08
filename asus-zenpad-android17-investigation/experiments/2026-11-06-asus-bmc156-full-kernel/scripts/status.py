from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
print(run('''from pathlib import Path
import json,subprocess
R=Path('/srv/android/asus-bmc156-full-kernel-r1');E=R/'evidence'
for n in ['build-status.json','supervisor.log']:
 p=E/n
 if p.exists():
  if n.endswith('.json'):
   d=json.loads(p.read_text());print(json.dumps({k:d.get(k) for k in ['pid','status','started','finished','exit','error','affinity','max_jobs']}))
  elif p.stat().st_size:print(n,p.read_text()[-1500:])
p=E/'Image.gz-dtb.log'
if p.exists():
 with p.open('rb') as f:
  f.seek(max(0,p.stat().st_size-5000));s=f.read().decode(errors='replace');print('\\n'.join(s.splitlines()[-10:]))
for l in subprocess.check_output(['ps','-eo','pid,ppid,etime,pcpu,psr,comm,args'],text=True).splitlines():
 if str(R) in l and ('python3 -B' in l or 'cc1 ' in l):print(l[:180])
'''))
