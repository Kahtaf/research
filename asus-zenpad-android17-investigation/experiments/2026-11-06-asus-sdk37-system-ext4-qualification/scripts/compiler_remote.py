import os,resource,pathlib,subprocess,json,hashlib,shutil
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=pathlib.Path;F=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106/fixture-r2');O=F/'compiler-bin';O.mkdir();d=[]
for name in ['cc1','collect2','as','ld']:
 s=subprocess.check_output(['/usr/bin/aarch64-linux-gnu-gcc','-print-prog-name='+name],text=True).strip();p=P(shutil.which(s)or s);q=O/name
 b=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copyfile(p,q);q.chmod(0o755);h=hashlib.sha256(q.read_bytes()).hexdigest();a=hashlib.sha256(p.read_bytes()).hexdigest();assert b==h==a;d.append(dict(source=str(p),copy=str(q),before=b,copied=h,after=a))
(F/'compiler-copy-receipt.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
