#!/usr/bin/env python3
"""One serial static C compile on the fixed builder, entirely in a fresh prefix."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import tarfile

R = Path(__file__).resolve().parents[1]
OLD = R.parent / '2026-11-07-asus-linux49-silent-single-cpu-probe'
REMOTE = '/srv/android/2026-11-07-asus-linux49-usb-ram-report-9342cbf1'


def main():
    run = json.loads((R / 'source/run.json').read_text())
    source = (R / 'source/init.c.in').read_text().replace('@RUN_ID@', run['run_id']).replace('@USB_SERIAL@', run['usb_serial']).replace('@VOLUME_ID@', run['run_id'].split('-')[0])
    assert '@' not in source
    (R / 'source/init.c').write_text(source)
    base = (OLD / 'artifacts/candidate.img').read_bytes()
    previous_full = (OLD / 'artifacts/candidate.p10.raw').read_bytes()
    assert hashlib.sha256(base).hexdigest() == '827d338c1733665c5adb40daa4a20505ec9ca7e2e586decd6069e2299bf4e062'
    assert previous_full == base + bytes(16740352 - len(base))
    assert hashlib.sha256(previous_full).hexdigest() == 'ad32e78548ec22d03685839858bcbccd163465125d4fe7c6b68f86dd19f65982'
    files = {str(p.relative_to(R)): p.read_bytes() for p in (R / 'source').iterdir() if p.is_file()}
    files['inputs/base.img'] = base
    files['inputs/install.py'] = (OLD / 'source/install.py').read_bytes()
    bundle = io.BytesIO()
    with tarfile.open(fileobj=bundle, mode='w') as t:
        for name, data in files.items():
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            t.addfile(info, io.BytesIO(data))
    spec = importlib.util.spec_from_file_location('fixed_builder', R.parent / '2026-11-06-asus-stock-only-ram-rescue-build/scripts/remote.py')
    transport = importlib.util.module_from_spec(spec); spec.loader.exec_module(transport)
    code = r'''from pathlib import Path
import contextlib,hashlib,io,json,os,resource,runpy,subprocess,sys,tarfile
r=Path(REMOTE);r.mkdir();os.chdir(r)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
for d in ['artifacts','evidence']:Path(d).mkdir()
os.environ.update(TMPDIR=str(r/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1794009600',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
cmd=['aarch64-linux-gnu-gcc','-static','-Os','-s','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wl,--build-id=none','-fno-ident','source/init.c','-o','artifacts/init']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
log=dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,compilations=1,parallelism=1,remote_prefix=str(r))
Path('evidence/build-log.json').write_text(json.dumps(log,indent=2)+'\n')
if p.returncode:raise RuntimeError(json.dumps(log))
sys.path.insert(0,str(r/'source'))
with open('evidence/package.stdout','w') as out,contextlib.redirect_stdout(out):runpy.run_path('source/package_probe.py',run_name='__main__')
owned=sum(p.stat().st_size for p in r.rglob('*') if p.is_file());assert owned<64*1024**2
log.update(owned_bytes=owned,max_owned_bytes=64*1024**2,affinity=sorted(os.sched_getaffinity(0)),memory_limit=512*1024**2)
Path('evidence/build-log.json').write_text(json.dumps(log,indent=2)+'\n')
names=['artifacts/candidate.img','artifacts/init','source/init.c','source/install.py','source/install.diff','evidence/manifest.json','evidence/build-log.json']
assert sum((r/n).stat().st_size for n in names)<32*1024**2
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
 for n in names:t.add(r/n,arcname=n)
'''.replace('REMOTE', repr(REMOTE))
    result = transport.call(code, bundle.getvalue(), timeout=150)
    (R / 'evidence/remote.stderr').write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors='replace'))
    assert len(result.stdout) < 32 * 1024**2
    allowed = {'artifacts/candidate.img','artifacts/init','source/init.c','source/install.py','source/install.diff','evidence/manifest.json','evidence/build-log.json'}
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as t:
        assert {p.name for p in t.getmembers()} == allowed
        assert all(p.isfile() for p in t.getmembers())
        t.extractall(R, filter='data')
    print((R / 'evidence/manifest.json').read_text())


if __name__ == '__main__':
    main()
