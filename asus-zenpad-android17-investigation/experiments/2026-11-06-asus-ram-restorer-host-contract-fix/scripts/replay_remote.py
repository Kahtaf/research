"""Create an owned Linux test fixture; never contacts the tablet."""
from pathlib import Path
import hashlib,io,json,shlex,subprocess,tarfile
R=Path(__file__).resolve().parents[1]
REMOTE='/srv/android/2026-11-06-asus-ram-restorer-host-contract-fix'
BASE='/srv/android/2026-11-06-asus-ram-original-recovery-restorer'
SSH=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
names=['source/host.py','source/generated_host_binding.py','tests/host_tests.py','tests/host_durability.py','tests/contract_tests.py']
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as tar:
    for name in names:tar.add(R/name,arcname=name)
code=r'''
from pathlib import Path
import hashlib,io,json,os,resource,shutil,subprocess,sys,tarfile
r=Path(REMOTE);b=Path(BASE);r.mkdir()
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(r,filter='data')
(r/'artifacts/candidate').mkdir(parents=True);(r/'evidence').mkdir()
names=['artifacts/original-recovery.payload','artifacts/candidate/UNARMED.p10.raw','artifacts/p10-restore','artifacts/session_server','source/host.py','source/p10_restore.c','tests/session_server.c','tests/storage.h']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(b/n) for n in names}
for n in names[:4]:
    shutil.copyfile(b/n,r/n)
    assert sha(r/n)==before[n]
os.chmod(r/'artifacts/session_server',0o700)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.chdir(r);results=[]
for test in ['tests/contract_tests.py','tests/host_tests.py','tests/host_durability.py']:
    p=subprocess.run(['python3','-B',test],text=True,capture_output=True,timeout=120)
    results.append(dict(command=['python3','-B',test],exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    (r/'evidence/replay.json').write_text(json.dumps(results,indent=2)+'\n')
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
after={n:sha(b/n) for n in names};assert before==after
result=dict(tests=results,original_pins=before,originals_unchanged=True,cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),device_operations=False,target_binaries_changed=False,phase_timing_physically_qualified=False)
(r/'evidence/result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
'''.replace('REMOTE',repr(REMOTE)).replace('BASE',repr(BASE))
p=subprocess.run(SSH+['python3 -B -c '+shlex.quote(code)],input=buf.getvalue(),capture_output=True,timeout=240)
(R/'evidence/remote-replay.stdout').write_bytes(p.stdout)
(R/'evidence/remote-replay.stderr').write_bytes(p.stderr)
if p.returncode:raise RuntimeError(p.stderr.decode() or p.stdout.decode())
result=json.loads(p.stdout)
(R/'evidence/remote-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'suites':[{k:v for k,v in t.items() if k in ('command','exit','stdout')} for t in result['tests']],'originals_unchanged':True},indent=2))
