#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path('/srv/android/lineage24');kernel=Path('/srv/android/asus-android17/kernel-bpf-fd')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={};repos={}
for repo in [kernel,root/'hardware/interfaces',root/'frameworks/base',root/'system/linkerconfig']:
 repos[str(repo)]=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
 names=set(subprocess.check_output(['git','-C',str(repo),'diff','--name-only'],text=True).splitlines())
 names.update(subprocess.check_output(['git','-C',str(repo),'ls-files','--others','--exclude-standard'],text=True).splitlines())
 for name in sorted(names):
  p=repo/name
  if p.is_file():files[str(p)]=sha(p)
for p in sorted((root/'device/asus/p00a').rglob('*')):
 if p.is_file():files[str(p)]=sha(p)
r=dict(revisions=repos,sha256=files,public_key_source='/srv/android/asus-device-product/debug-adb-public-key',private_key_read=False)
Path(sys.argv[1]).write_text(json.dumps(r,indent=2)+'\n')
print(len(files),'source inputs recorded')
