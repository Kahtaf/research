from pathlib import Path
import subprocess as s,shutil,json,hashlib,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1');A=Path('/srv/android/lineage24');I=R/'sdk';I.mkdir(exist_ok=False)
rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for repo,paths in [('bionic',['libc/include','libc/kernel/uapi','libc/kernel/android/uapi']),('hardware/libhardware',['include','include_all']),('system/core',['libcutils/include','libsystem/include'])]:
 rev=s.check_output(['git','-C',str(A/repo),'rev-parse','HEAD'],text=True).strip()
 dest=I/'headers'/repo;dest.mkdir(parents=True)
 p=s.Popen(['git','-C',str(A/repo),'archive',rev,'--']+paths,stdout=s.PIPE)
 s.run(['tar','xf','-','-C',str(dest)],stdin=p.stdout,check=True);assert p.wait()==0
 rows.append(dict(source=repo,commit=rev,paths=paths))
(I/'lib').mkdir()
for name in ['libc.so','libdl.so','libm.so']:
 p=Path('/srv/android/asus-android17-runtime-prereqs/inputs/root/system/lib64')/name
 if p.exists():shutil.copyfile(p,I/'lib'/name);rows.append(dict(source=str(p),sha256=sha(p),destination='lib/'+name))
for name in ['crtbegin_so','crtend_so']:
 p=A/f'out/soong/.intermediates/bionic/libc/{name}/android_arm64_armv8-a/{name}.o'
 assert p.exists(),p
 data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==sha(p)
 (I/'lib'/(name+'.o')).write_bytes(data);rows.append(dict(source=str(p),sha256=sha(p),destination='lib/'+name+'.o'))
for p in sorted((I/'headers').rglob('*')):
 if p.is_file() and not p.is_symlink():rows.append(dict(path=str(p.relative_to(I)),sha256=sha(p)))
(R/'evidence/sdk-inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
for p in ['hardware/interfaces/sensors/1.0/default/Sensors.cpp','hardware/interfaces/sensors/1.0/default/Android.bp','hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED','hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED','build/make/core/version_defaults.mk']:
 f=A/p
 if f.exists():
  dest=R/'sdk/reference'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
print('Frozen SDK inputs',len(rows))
print(s.run(['sh','-c','command -v qemu-aarch64-static || command -v qemu-aarch64 || true'],capture_output=True,text=True).stdout)
