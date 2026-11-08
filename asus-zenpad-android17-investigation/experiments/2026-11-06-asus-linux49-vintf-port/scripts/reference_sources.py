from pathlib import Path
import subprocess,json,base64,hashlib
r={}
for d in ['/srv/android/reference-kernel','/srv/android/lineage24/kernel/asus/p00a-fd','/srv/android/asus-android17/kernel-bpf-fd']:
 r[d]={}
 for args in [['rev-parse','HEAD'],['ls-tree','--name-only','HEAD'],['ls-tree','-r','--name-only','HEAD','android','kernel/configs'],['log','-1','--format=fuller']]:
  z=subprocess.run(['git','-C',d]+args,capture_output=True,text=True,timeout=15);r[d][' '.join(args)]=z.stdout[:12000]+z.stderr[:1000]
print(json.dumps(r,indent=2))
