from remote import R,REMOTE,call
import sys
p=call('import runpy;runpy.run_path('+repr(REMOTE+'/scripts/build_remote.py')+',run_name="__main__")')
(R/'evidence/remote-build.stdout').write_bytes(p.stdout);(R/'evidence/remote-build.stderr').write_bytes(p.stderr)
print(p.stdout.decode());print(p.stderr.decode(),file=sys.stderr);sys.exit(p.returncode)
