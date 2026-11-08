"""New bounded SSH Linux fixture; no device, privilege or lifecycle operations.

Private key is passed by pathname to ssh only, never opened by this program.
The remote directory must not preexist. All remote mutations are inside it.
"""
import hashlib
import io
import json
import os
import shlex
import subprocess
import tarfile
from pathlib import Path

R=Path(__file__).resolve().parents[1]
S=R.parent/'2026-11-06-asus-android17-target-rescue'
REMOTE='/srv/android/asus-target-rescue-review'
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),
     '-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15',
     '-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556',
     '-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),
     'android@IP_REDACTED']

def main():
    entries={}
    for name in ['source/rescue.c','source/common.h','source/sha256.h','source/client.py','source/manifest.py',
                 'tests/test_server.c','tests/test_adapters.py',
                 'artifacts/candidate-delivery/rescue-sepolicy','artifacts/candidate-delivery/file_contexts.bin']:
        entries[name]=(S/name).read_bytes()
    entries['scripts/review_sessions.py']=(R/'scripts/review_sessions.py').read_bytes()
    toolhashes={name:hashlib.sha256((S/'artifacts/tools-delivery'/name).read_bytes()).hexdigest()
                for name in ['policy_constraints','context_lookup']}
    entries['tool-pins.json']=(json.dumps(toolhashes,indent=2)+'\n').encode()
    entries['README.md']=b'Isolated bounded offline review fixture. No target operations. Source snapshots are read-only inputs.\n'
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as tar:
        for name,data in entries.items():
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644
            tar.addfile(info,io.BytesIO(data))
    remote_setup='import io,os,sys,tarfile,pathlib; r=pathlib.Path('+repr(REMOTE)+'); r.mkdir(); os.chdir(r); tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter="data"); (r/"evidence").mkdir(); (r/"artifacts").mkdir(exist_ok=True)'
    setup=subprocess.run(SSH+['python3 -B -c '+shlex.quote(remote_setup)],input=buf.getvalue(),capture_output=True,timeout=30)
    (R/'evidence/linux-setup.stdout').write_bytes(setup.stdout)
    (R/'evidence/linux-setup.stderr').write_bytes(setup.stderr)
    if setup.returncode:raise RuntimeError('Fresh fixture setup failed; retained output; do not overwrite/retry')
    code='''import os,resource,subprocess,json,hashlib,pathlib,sys
r=pathlib.Path('/srv/android/asus-target-rescue-review');os.chdir(r)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(90,90))
os.environ['TMPDIR']=str(r/'artifacts');os.environ['PYTHONDONTWRITEBYTECODE']='1'
cmd=['gcc','-O2','-Wall','-Wextra','-Wno-unused-function','-Wno-misleading-indentation','tests/test_server.c','-o','artifacts/test_server']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
(r/'evidence/compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2))
if p.returncode:sys.exit(p.returncode)
os.environ['RESCUE_TEST_SERVER']=str(r/'artifacts/test_server')
p=subprocess.run(['python3','-B','scripts/review_sessions.py'],capture_output=True,text=True,timeout=45)
(r/'evidence/session-tests.stdout').write_text(p.stdout);(r/'evidence/session-tests.stderr').write_text(p.stderr)
toolroot=pathlib.Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
for name,want in json.loads((r/'tool-pins.json').read_text()).items():
 assert hashlib.sha256((toolroot/name).read_bytes()).hexdigest()==want
policy=str(r/'artifacts/candidate-delivery/rescue-sepolicy');contexts=str(r/'artifacts/candidate-delivery/file_contexts.bin');checks=[]
for part,name,t in [(9,'boot','rescue_boot_device'),(10,'recovery','rescue_recovery_device'),(25,'system','rescue_system_device')]:
 for cl,perms in [('lnk_file','read,getattr'),('blk_file','open,read,getattr,ioctl')]:
  cmd=[str(toolroot/'policy_constraints'),policy,'u:r:os_rescue:s0','u:object_r:'+t+':s0',cl,perms]
  q=subprocess.run(cmd,capture_output=True,text=True,timeout=10);checks.append(dict(command=cmd,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr))
 cmd=[str(toolroot/'context_lookup'),contexts,'/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/'+name,'120777']
 q=subprocess.run(cmd,capture_output=True,text=True,timeout=10);checks.append(dict(command=cmd,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr))
(r/'evidence/policy-alias-queries.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(dict(test_returncode=p.returncode,cpu_affinity=sorted(os.sched_getaffinity(0)),address_space_limit=resource.getrlimit(resource.RLIMIT_AS),fixture=str(r))))
sys.exit(p.returncode)
'''
    result=subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],capture_output=True,timeout=110)
    (R/'evidence/linux-run.stdout').write_bytes(result.stdout)
    (R/'evidence/linux-run.stderr').write_bytes(result.stderr)
    receipt={'remote':REMOTE,'setup_returncode':setup.returncode,'run_returncode':result.returncode,
             'inputs':{name:hashlib.sha256(data).hexdigest() for name,data in entries.items()},
             'resource_limits':'one allowed CPU, RLIMIT_AS 1GiB, RLIMIT_CPU 90 seconds, sequential gcc, no guest/no network service',
             'scope':'new review fixture only; existing tools read-only and hash-checked; no device/private material accessed'}
    (R/'evidence/linux-run-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Capture only our new bounded text evidence; preserve all outputs, including failures.
    get=subprocess.run(SSH+['tar -C '+shlex.quote(REMOTE)+' -cf - evidence'],capture_output=True,timeout=30)
    if get.returncode:raise RuntimeError('evidence collection failed')
    with tarfile.open(fileobj=io.BytesIO(get.stdout)) as tar:
        for member in tar.getmembers():
            if member.isfile():
                assert member.name.startswith('evidence/') and member.size<2*1024*1024
                (R/'evidence'/('linux-'+Path(member.name).name)).write_bytes(tar.extractfile(member).read())
    print(json.dumps(receipt,indent=2))
    if result.returncode:raise RuntimeError('Review tests failed; all runs retained')

if __name__=='__main__':main()
