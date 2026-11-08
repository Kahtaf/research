"""Existing builder transport only; all writes stay in the new review fixture."""
from pathlib import Path
import io,tarfile,subprocess,shlex,sys,json
R=Path(__file__).resolve().parents[1]
REMOTE='/srv/android/2026-11-06-stock-review'
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
if sys.argv[1]=='start':
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w') as t:
        for name in ['run_linux.py','host_edges.py','readonly_reconciliation.py']:t.add(R/'scripts'/name,arcname='scripts/'+name)
    code='from pathlib import Path;import sys,tarfile; p=Path('+repr(REMOTE)+');p.mkdir();(p/"artifacts").mkdir();(p/"evidence").mkdir();tarfile.open(fileobj=sys.stdin.buffer,mode="r|*").extractall(p,filter="data")'
    subprocess.run(SSH+['python3 -c '+shlex.quote(code)],input=b.getvalue(),check=True)
    with (R/'evidence/remote-run.stdout').open('w') as out,(R/'evidence/remote-run.stderr').open('w') as err:
        p=subprocess.run(SSH+['python3 -B '+shlex.quote(REMOTE+'/scripts/run_linux.py')],stdout=out,stderr=err)
    print('remote review exit',p.returncode);sys.exit(p.returncode)
elif sys.argv[1]=='collect':
    p=subprocess.run(SSH+['tar -C '+shlex.quote(REMOTE)+' -cf - evidence'],capture_output=True,check=True)
    dest=R/'linux-results';dest.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:t.extractall(dest,filter='data')
    print('Collected compact evidence only')
