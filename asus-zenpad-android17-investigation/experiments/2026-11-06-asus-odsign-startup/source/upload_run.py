from pathlib import Path
import base64,subprocess,sys
from remote import BASE
R=Path(__file__).resolve().parents[1];files={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in (R/'source').glob('*') if p.is_file()}
script="from pathlib import Path\nimport base64\nR=Path('/srv/android/asus-odsign-startup-20261106')\nfiles="+repr(files)+"\nfor n,b in files.items():\n p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))\nexec(compile((R/'source/prepare.py').read_text(),str(R/'source/prepare.py'),'exec'))\n"
raise SystemExit(subprocess.run(BASE+['python3 -'],input=script.encode()).returncode)
