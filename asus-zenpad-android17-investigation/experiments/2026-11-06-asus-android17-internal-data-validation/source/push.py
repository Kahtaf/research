from remote import SSH
from pathlib import Path
import subprocess,sys,tarfile,io
R=Path(__file__).resolve().parents[1];b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w:gz') as t:
 for name in sys.argv[1:]:t.add(R/name,arcname=name)
p=subprocess.run(SSH+['tar -xzf - -C /srv/android/asus-internal-data-validation'],input=b.getvalue());sys.exit(p.returncode)
