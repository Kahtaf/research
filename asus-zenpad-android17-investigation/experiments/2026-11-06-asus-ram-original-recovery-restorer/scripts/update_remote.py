from pathlib import Path
import io,tarfile,sys,json
from remote import R,REMOTE,call
revision=sys.argv[1];assert revision.isalnum()
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as t:
 for dirname in ['source','tests','scripts']:
  for p in (R/dirname).rglob('*'):
   if p.is_file() and not p.name.startswith('._') and '__pycache__' not in str(p):t.add(p,arcname=str(p.relative_to(R)))
code='''import pathlib,os,sys,tarfile,io
r=pathlib.Path(REMOTE);os.chdir(r)
archive=r/'revisions'/REVISION;archive.mkdir(parents=True,exist_ok=False)
(archive/'artifacts').mkdir();(archive/'evidence').mkdir();(archive/'source').mkdir()
for name in ['os-rescue','policy_build','restore-sepolicy','file_contexts.bin','rescue-proxy','core.cpio.gz','core-entries.json','p10-restore','p10-restore-reproduction','candidate','core_tests','session_server','legacy-reproduction','test_server','policy_audit','concat-probe','concat-test.initramfs','reproduction']:
 p=r/'artifacts'/name
 if p.exists():p.rename(archive/'artifacts'/name)
for p in (r/'evidence').iterdir():
 if p.name not in ['input-pins.json']:p.rename(archive/'evidence'/p.name)
for p in (r/'source').iterdir():
 if p.is_file():(archive/'source'/p.name).write_bytes(p.read_bytes())
tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())).extractall(filter='data')
'''.replace('REMOTE',repr(REMOTE)).replace('REVISION',repr(revision))
p=call(code,buf.getvalue());assert p.returncode==0
p=call('import runpy;runpy.run_path('+repr(REMOTE+'/scripts/build_remote.py')+',run_name="__main__")',timeout=300)
(R/'evidence'/('remote-'+revision+'.stdout')).write_bytes(p.stdout);(R/'evidence'/('remote-'+revision+'.stderr')).write_bytes(p.stderr)
print(p.stdout.decode());sys.exit(p.returncode)
