"""Transport only to the existing build VM; never to the tablet."""
from pathlib import Path
import io,json,hashlib,subprocess,tarfile,shlex,sys
R=Path(__file__).resolve().parents[1];W=R.parent
REMOTE='/srv/android/2026-11-06-asus-ram-original-recovery-restorer'
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
def call(code,data=None,timeout=240):
 p=subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],input=data,capture_output=True,timeout=timeout)
 if p.returncode:print(p.stderr.decode(),file=sys.stderr)
 return p
def setup():
 T=W/'2026-11-06-asus-android17-target-rescue/artifacts/tools-delivery'
 names=['rescue-proxy','sefcontext_compile','policy_constraints','policy_query','policy_inspect','context_lookup']
 (R/'tool-pins.json').write_text(json.dumps({n:hashlib.sha256((T/n).read_bytes()).hexdigest() for n in names},indent=2)+'\n')
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w') as t:
  for p in R.rglob('*'):
   if p.is_file() and not p.name.startswith('._') and '__pycache__' not in str(p):t.add(p,arcname=str(p.relative_to(R)))
 code='import pathlib,os,tarfile,io,sys;r=pathlib.Path('+repr(REMOTE)+');r.mkdir();os.chdir(r);tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter="data")'
 p=call(code,buf.getvalue());assert p.returncode==0
 p=call('import runpy;runpy.run_path('+repr(REMOTE+'/scripts/build_remote.py')+',run_name="__main__")')
 (R/'evidence/remote-build.stdout').write_bytes(p.stdout);(R/'evidence/remote-build.stderr').write_bytes(p.stderr)
 print(p.stdout.decode());return p.returncode
if __name__=='__main__':sys.exit(setup())
