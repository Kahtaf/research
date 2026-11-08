"""Run only reviewed local fixture/PLAN_ONLY code, with external paths blocked."""
import os
from pathlib import Path
import resource
import runpy
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
target = Path(sys.argv[1]).resolve()
allowed = {
    ROOT / 'tests/fake_shell.py',
    ROOT / 'source/transport.py',
}
assert target in allowed
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
for name in ('RLIMIT_AS', 'RLIMIT_DATA', 'RLIMIT_RSS'):
    try:
        resource.setrlimit(getattr(resource, name), (1024**3, 1024**3))
    except (ValueError, OSError):
        pass
sys.dont_write_bytecode = True

def audit(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec',
                 'socket.connect', 'socket.bind', 'socket.getaddrinfo'):
        raise RuntimeError('Blocked external operation: ' + event)
    if event == 'socket.__new__' and args[1] != socket.AF_UNIX:
        raise RuntimeError('Only AF_UNIX permitted')
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes, os.PathLike)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            if not Path(path).absolute().is_relative_to(ROOT):
                raise RuntimeError('Write outside review spike')

sys.addaudithook(audit)
sys.argv = [str(target), *sys.argv[2:]]
runpy.run_path(str(target), run_name='__main__')
