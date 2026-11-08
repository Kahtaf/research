"""Offline, sequential, one process at a time; no device/network/build commands."""
from pathlib import Path
import subprocess,sys,json,hashlib,time
S=Path(__file__).resolve().parents[1]
results=[]
for name in ['extract.py','audit_static.py','crypto_details.py','check_filesystem.py','emulate_recovery.py']:
 start=time.monotonic();r=subprocess.run([sys.executable,'-B',str(S/'source'/name)],capture_output=True,text=True,timeout=45)
 results.append(dict(script=name,returncode=r.returncode,seconds=round(time.monotonic()-start,3),stdout=r.stdout,stderr=r.stderr))
 if r.returncode:break
out={'passed':all(x['returncode']==0 for x in results)and len(results)==5,'checks':results,'limits':'Selected reads only; no full SYSTEM hash/copy; synthetic emulation only; no physical effects.'}
(S/'evidence/checks.json').write_text(json.dumps(out,indent=2)+'\n')
pins={str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['source','inputs','evidence'] for p in sorted((S/folder).glob('*')) if p.is_file() and p.name!='artifact-sha256.json'}
(S/'evidence/artifact-sha256.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({'passed':out['passed'],'scripts':len(results),'pinned_files':len(pins)}));sys.exit(0 if out['passed'] else 1)
