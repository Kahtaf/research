from pathlib import Path
import json,shutil,subprocess,hashlib,resource
R=Path('/srv/android/asus-genuine-service-runtime');P=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/boot-r2'
shutil.copytree(R/'inputs/boot-r1',I,symlinks=True)
shutil.copytree(P/'inputs/observer-r1',R/'inputs/observer-r1',symlinks=True)
cmd=json.loads((P/'evidence/observer-compile.json').read_text())['command']
cmd=[x.replace(str(P/'inputs/observer-r1'),str(R/'inputs/observer-r1')).replace(str(P/'source/observer.c'),str(R/'source/observer.c')).replace(str(P/'artifacts/observer'),str(I/'root/system/bin/firstboot-observer')).replace(str(P/'inputs/early-r1/root/system/lib64'),str(I/'root/system/lib64')) for x in cmd]
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(cmd,capture_output=True,text=True,timeout=60,preexec_fn=limit);(R/'evidence/observer-compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
f=I/'root/system/etc/init/hw/init.rc';old=f.read_text();needle='    start hwservicemanager\n';assert old.count(needle)==1;new=old.replace(needle,needle+'    # Fixture diagnostic only: preserve subsequent mandatory self-tests.\n    exec_start firstboot-observer\n');f.write_text(new)
(R/'evidence/observer-adaptation.json').write_text(json.dumps(dict(before=hashlib.sha256(old.encode()).hexdigest(),after=hashlib.sha256(new.encode()).hexdigest(),source=hashlib.sha256((R/'source/observer.c').read_bytes()).hexdigest(),elf=hashlib.sha256((I/'root/system/bin/firstboot-observer').read_bytes()).hexdigest(),purpose='Read-only process, property and real binder IPC measurements before unchanged mandatory self-tests; inherited allowed/denied diagnostic property probes'),indent=2))
print('observer prepared')
