from pathlib import Path
import json,shutil,subprocess,resource,hashlib
R=Path('/srv/android/asus-genuine-service-runtime');I=R/'inputs/boot-r5';shutil.copytree(R/'inputs/boot-r3',I,symlinks=True)
cmd=json.loads((R/'evidence/observer-compile.json').read_text())['command'];cmd=[x.replace('/boot-r2/','/boot-r5/') for x in cmd]
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(cmd,capture_output=True,text=True,preexec_fn=limit,timeout=60);(R/'evidence/observer-r5-compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
shutil.copy2(R/'source/observer.c',I/'observer.c');print('probe r5 prepared')
