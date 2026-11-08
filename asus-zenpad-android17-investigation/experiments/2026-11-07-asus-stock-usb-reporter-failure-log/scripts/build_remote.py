"""One explicitly authorized corrected compile; fixed SSH, fresh owned prefix."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
attempt = ROOT / 'evidence/compile-2-attempt.json'
assert (ROOT / 'evidence/compile-1-build-log.json').exists()
assert not attempt.exists(), 'One authorized corrected compile only'
assert not (ROOT / 'artifacts/init').exists()
prefix = '/srv/android/2026-11-07-asus-stock-usb-reporter-failure-log-' + uuid.uuid4().hex
source = (ROOT / 'source/init.c').read_bytes()
receipt = dict(remote_prefix=prefix, source_sha256=hashlib.sha256(source).hexdigest(), compile_attempts=1, attempt_number=2, authorization='User explicitly allowed one corrected compile after the first failed on ignored logging write results.')
attempt.write_text(json.dumps(receipt, indent=2) + '\n')
spec = importlib.util.spec_from_file_location('fixed_builder', ROOT.parent / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
bundle = io.BytesIO()
with tarfile.open(fileobj=bundle, mode='w') as t:
    info = tarfile.TarInfo('source/init.c')
    info.size = len(source)
    info.mode = 0o644
    t.addfile(info, io.BytesIO(source))
code = r'''from pathlib import Path
import hashlib,io,json,os,resource,subprocess,sys,tarfile
r=Path(PREFIX);r.mkdir();os.chdir(r)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(90,90))
resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())) as t:
 assert len(t.getmembers())==1 and t.getmembers()[0].name=='source/init.c' and t.getmembers()[0].isfile()
 t.extractall(filter='data')
for d in ['artifacts','evidence']:Path(d).mkdir()
os.environ.update(TMPDIR=str(r/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1794009600',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
cmd=['aarch64-linux-gnu-gcc','-static','-Os','-s','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wl,--build-id=none','-fno-ident','source/init.c','-o','artifacts/init']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
log=dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,compilations=1,parallelism=1,remote_prefix=str(r),affinity=sorted(os.sched_getaffinity(0)),memory_limit=512*1024**2,cpu_seconds_limit=90,file_bytes_limit=32*1024**2,process_count_limit_changed=False,kernel_build=False,active_build_inspection=False)
log['owned_bytes']=sum(p.stat().st_size for p in r.rglob('*') if p.is_file())
assert log['owned_bytes']<64*1024**2
if not p.returncode:log['init_sha256']=hashlib.sha256(Path('artifacts/init').read_bytes()).hexdigest()
Path('evidence/build-log.json').write_text(json.dumps(log,indent=2)+'\n')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for n in ['evidence/build-log.json']+(['artifacts/init'] if not p.returncode else []):t.add(r/n,arcname=n)
'''.replace('PREFIX', repr(prefix))
result = subprocess.run(transport.SSH + ['python3 -B -c ' + __import__('shlex').quote(code)], input=bundle.getvalue(), capture_output=True, timeout=150)
(ROOT / 'evidence/remote.stderr').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode(errors='replace')
assert len(result.stdout) < 4*1024**2
with tarfile.open(fileobj=io.BytesIO(result.stdout)) as t:
    names = {p.name for p in t.getmembers()}
    assert names in ({'evidence/build-log.json'}, {'evidence/build-log.json', 'artifacts/init'})
    assert all(p.isfile() for p in t.getmembers())
    t.extractall(ROOT, filter='data')
log = json.loads((ROOT / 'evidence/build-log.json').read_text())
assert log['returncode'] == 0, log
print(json.dumps(log, indent=2))
