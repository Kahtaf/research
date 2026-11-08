from pathlib import Path
import subprocess,tarfile
P=Path(__file__).resolve().parent.parent;ns={};t=(P/'scripts/remote.py').read_text();exec(t[:t.index('r=subprocess')],ns)
f=P/'evidence/remote-capture.tar.gz'
with f.open('wb') as out:subprocess.run(ns['SSH']+['tar -C /srv/android/asus-sdk37-lmkd-functional -czf - evidence source run-kernel-negative-r1'],stdout=out,check=True)
with tarfile.open(f) as a:a.extractall(P/'evidence/remote',filter='data')
