"""Upload only this kit; no launch, approval, or changes to any ancestor."""
from pathlib import Path
import io,subprocess,sys,tarfile
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from remote import SSH
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as tar:
 for folder in ['scripts','inputs','tests']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(x.startswith('TEST_ONLY-') for x in p.parts):tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
# Exclusive kit creation; never overwrite a deployed kit or attempt.
command='umask 022; mkdir /srv/android/asus-reviewed-build-kit/r7 && tar -xzf - -C /srv/android/asus-reviewed-build-kit/r7'
r=subprocess.run(SSH+[command],input=buf.getvalue(),capture_output=True)
print('bytes',len(buf.getvalue()),'exit',r.returncode,r.stdout.decode(),r.stderr.decode());r.check_returncode()
