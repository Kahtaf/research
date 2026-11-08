"""Reject standalone build invocation, stale launch state, and foreign lock FDs."""
import fcntl
import os
from pathlib import Path
import sys
from integrate import need, read, sha, verify_pins
root = Path(sys.argv[1]).resolve()
verify_pins(root)
plan = read(root / 'inputs/plan.json')
launch = read(root / 'attempt/launch.json')
fd = int(os.environ['REVIEWED_BUILD_LOCK_FD'])
need(os.getppid() != 1, 'No supervised launch')
# Python is a child of build.sh; its parent's PPid must be the recorded supervisor.
parent_status = Path('/proc/' + str(os.getppid()) + '/status').read_text().splitlines()
parent_ppid = int(next(l.split(':', 1)[1] for l in parent_status if l.startswith('PPid:')))
need(parent_ppid == launch['supervisor_pid'], 'Build is not child of recorded supervisor')
need(os.fstat(fd).st_ino == Path(plan['lock']).stat().st_ino == launch['lock_inode'], 'Wrong lock inode')
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
with Path(plan['lock']).open('r+') as independent:
    try:
        fcntl.flock(independent, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        raise RuntimeError('Shared full-build lock is not held')
need(not (root / 'attempt/FAILED.json').exists(), 'Failed attempt cannot launch')
# Independent exclusive consumption, not a ready flag. No second direct invocation.
with (root / 'attempt/build-consumed').open('x') as out:
    out.write(str(os.getpid()) + '\n')
