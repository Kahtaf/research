from pathlib import Path
import json,subprocess
from vm import R,channel
base=(R/'scripts/build_remote.py').read_text()
prefix=base[:base.index("assert not (E/'build-status.json').exists()")]
body=base[base.index(' # Isolate only after helper fits;'):base.index('except BaseException as exc:')]
body=body.replace("['cp','-a','--reflink=always'","['cp','-a','--reflink=auto'")
body=body.replace("method='cp -a --reflink=always; independent inodes; nested repositories preserved'","method='reflink unsupported (Operation not supported); authorized cp -a --reflink=auto full copies, independent inodes; nested repositories preserved'")
script=prefix+'''s=json.loads((E/'build-status.json').read_text())
assert s['helper_compiles']==1 and s['kernel_builds']==0 and s['status']=='failed'
assert json.loads((E/'compiler-receipt.json').read_text())['fits']
# Filesystem metadata only, before any owned partial-copy removal.
needed=sum(p.stat().st_size for name in ['kernel','out'] for p in (B/name).rglob('*') if p.is_file() and not p.is_symlink())
usage=shutil.disk_usage(B)
save('space-receipt.json',dict(required_logical_bytes=needed,free_bytes=usage.free,reserve_bytes=2*1024**3,adequate=usage.free>needed+2*1024**3,source='filesystem stat metadata only'))
assert usage.free>needed+2*1024**3,'STOP: insufficient free space'
assert not (R/'out').exists()
# Delete only this attempt's incomplete unsupported-clone destination.
assert R.name=='asus-pid1-fifo-loop-control-20261108-f53fadc2'
shutil.rmtree(R/'kernel')
(E/'first-attempt-build-status.json').write_text(json.dumps(s,indent=2)+'\\n')
s.update(status='running',error=None,copy_fallback='user-authorized independent full copies; no new helper compile')
save('build-status.json',s)
try:
'''+body+base[base.index('except BaseException as exc:'):]
(R/'scripts/resume_remote.py').write_text(script)
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/resume.stdout').write_text(p.stdout);(R/'evidence/resume.stderr').write_text(p.stderr);print(p.stdout);print(p.stderr);p.check_returncode()
