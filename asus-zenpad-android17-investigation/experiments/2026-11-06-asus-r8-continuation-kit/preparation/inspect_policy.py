exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
print(m.run(r'''
from pathlib import Path
import json,subprocess,ctypes.util
R=Path('/srv/android/asus-sdk37-lmkd-functional/inputs/fixture-r20/root')
print(json.dumps(dict(files=[str(p) for p in R.glob('**/etc/selinux/*') if p.is_file()],help=subprocess.run(['/srv/android/lineage24/out/host/linux-x86/bin/sefcontext_compile','-h'],capture_output=True,text=True).__dict__,lib=ctypes.util.find_library('selinux')),default=str,indent=2))
'''))
