"""Upload only this kit's files; preserve existing remote revisions/evidence."""
from pathlib import Path
import io,json,subprocess,tarfile
from remote import SSH
R=Path(__file__).resolve().parents[1]
data=io.BytesIO()
with tarfile.open(fileobj=data,mode='w:gz') as tar:
 for folder in ['scripts','inputs','tests']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(x.startswith('TEST_ONLY-') for x in p.parts):tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
command="umask 022; mkdir -p /srv/android/asus-reviewed-build-kit/r3; test ! -e /srv/android/asus-reviewed-build-kit/r3/attempt && tar -xzf - -C /srv/android/asus-reviewed-build-kit/r3"
r=subprocess.run(SSH+[command],input=data.getvalue(),capture_output=True)
print(json.dumps({'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),'archive_bytes':len(data.getvalue())}));r.check_returncode()
