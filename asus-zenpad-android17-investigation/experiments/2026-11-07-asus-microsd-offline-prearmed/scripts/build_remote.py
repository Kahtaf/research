"""One small owned compile, focused fixtures, and fetch. No platform inputs."""
from pathlib import Path
import importlib.util
import io
import json
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/srv/android/asus-microsd-offline-prearmed-20261107-impl1'
spec = importlib.util.spec_from_file_location('fixed_remote', ROOT.parent / '2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w') as archive:
    for group in ('source', 'scripts', 'inputs'):
        for p in sorted((ROOT / group).iterdir()):
            if p.is_file():
                archive.add(p, arcname=str(p.relative_to(ROOT)))
code = '''
from pathlib import Path
import os, io, sys, tarfile, resource, subprocess, json, hashlib
r=Path(REMOTE);r.mkdir();os.chdir(r)
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
Path('artifacts').mkdir();Path('evidence').mkdir()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(r/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',SOURCE_DATE_EPOCH='1794009600')
logs=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 Path('evidence/build.json').write_text(json.dumps(logs,indent=2)+'\\n')
 if p.returncode: raise RuntimeError(p.stderr+p.stdout)
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wno-unused-function','-fno-ident','-Wl,--build-id=none']
run(['python3','-B','scripts/check_bodies.py'])
run(['gcc',*flags,'source/test_offline.c','-o','artifacts/test_offline'])
run(['artifacts/test_offline'])
run(['gcc',*flags,'source/test_phase.c','-o','artifacts/test_phase'])
run(['artifacts/test_phase'])
run(['aarch64-linux-gnu-gcc',*flags,'-c','source/rescue.c','-o','artifacts/rescue.aarch64.o'])
run(['aarch64-linux-gnu-gcc','-static',*flags,'source/sd_frontend.c','-o','artifacts/sd_frontend.aarch64'])
run(['aarch64-linux-gnu-readelf','-h','-l','artifacts/sd_frontend.aarch64'])
p=Path('artifacts/sd_frontend.aarch64');b=p.read_bytes()
assert b[:4]==b'\\x7fELF' and int.from_bytes(b[18:20],'little')==183
phoff=int.from_bytes(b[32:40],'little');ents=int.from_bytes(b[54:56],'little');n=int.from_bytes(b[56:58],'little')
assert all(int.from_bytes(b[phoff+i*ents:phoff+i*ents+4],'little') not in (2,3) for i in range(n))
obj=Path('artifacts/rescue.aarch64.o').read_bytes();assert obj[:4]==b'\\x7fELF' and int.from_bytes(obj[18:20],'little')==183 and int.from_bytes(obj[16:18],'little')==1
Path('evidence/artifact.json').write_text(json.dumps(dict(daemon_object=dict(bytes=len(obj),sha256=hashlib.sha256(obj).hexdigest(),machine='AArch64',type='relocatable'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),machine='AArch64',static_no_interp_or_dynamic=True,parallelism=1,owned_prefix=str(r),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('source').iterdir() if p.is_file()},physical_validation=False),indent=2)+'\\n')
print('FOCUSED_CASES_AND_STATIC_AARCH64_COMPILE_PASS')
'''.replace('REMOTE', repr(REMOTE))
result = transport.call(code, buf.getvalue(), timeout=240)
(ROOT / 'evidence/remote.stdout').write_bytes(result.stdout)
(ROOT / 'evidence/remote.stderr').write_bytes(result.stderr)
print(result.stdout.decode(), end='')
print(result.stderr.decode(), end='', file=sys.stderr)
# Fetch own evidence even on compile failure; no external sources or inventory.
fetch = '''
from pathlib import Path
import sys,tarfile
r=Path(REMOTE)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for group in ('evidence','artifacts'):
  for p in sorted((r/group).iterdir()):
   if p.is_file() and (group=='evidence' or p.name in ('sd_frontend.aarch64','rescue.aarch64.o')):
    assert p.stat().st_size<16*1024**2;t.add(p,arcname=str(p.relative_to(r)))
'''.replace('REMOTE', repr(REMOTE))
f = transport.call(fetch, timeout=45)
if f.returncode:
    raise RuntimeError(f.stderr.decode())
with tarfile.open(fileobj=io.BytesIO(f.stdout)) as archive:
    archive.extractall(ROOT, filter='data')
if result.returncode:
    raise RuntimeError('owned compile/test failed; see evidence')
