from pathlib import Path
import base64,datetime,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
rp=W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec=importlib.util.spec_from_file_location('product_kit_remote',rp);remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
source=(R/'source/init.c').read_bytes()
script=r'''from pathlib import Path
import base64,datetime,gzip,hashlib,json,os,shutil,subprocess
R=Path('/srv/android/asus-linux49-runnable-timer-format-fix-20261107-bee07d4f')
assert not R.exists(),'Fresh owned prefix required'
R.mkdir();[(R/n).mkdir() for n in ['source','tmp','artifacts','evidence']]
source=base64.b64decode(SOURCE);(R/'source/init.c').write_bytes(source)
sha=lambda d:hashlib.sha256(d).hexdigest()
cc=shutil.which('aarch64-linux-gnu-gcc');assert cc
version=subprocess.run([cc,'--version'],capture_output=True,text=True,check=True).stdout
assert version.splitlines()[0]=='aarch64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0'
assert sha(Path(cc).resolve().read_bytes())=='cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a'
cmd=[cc,'-static','-Os','-s','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Wall','-Wextra','-o',str(R/'artifacts/init'),str(R/'source/init.c')]
env=dict(os.environ,TMPDIR=str(R/'tmp'))
q=subprocess.run(cmd,capture_output=True,text=True,env=env)
log='$ '+' '.join(cmd)+'\n'+q.stdout+q.stderr
(R/'evidence/compile-1.log').write_text(log)
receipt=dict(command=cmd,exit=q.returncode,compiler=cc,compiler_sha256=sha(Path(cc).resolve().read_bytes()),compiler_version=version,source_sha256=sha(source),static=True,kernel_copy_or_build=False,rlimit_as_added=False,at=datetime.datetime.now(datetime.timezone.utc).isoformat())
if q.returncode==0:
 data=(R/'artifacts/init').read_bytes();receipt.update(binary_bytes=len(data),binary_sha256=sha(data),binary_gzip_bytes=len(gzip.compress(data,compresslevel=9,mtime=0)))
(R/'evidence/compiler-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
files=['source/init.c','evidence/compile-1.log','evidence/compiler-receipt.json']+(['artifacts/init'] if q.returncode==0 else [])
print(json.dumps({n:base64.b64encode((R/n).read_bytes()).decode() for n in files}))
'''.replace('SOURCE',repr(base64.b64encode(source).decode()))
dispatch='compile-dispatch.json'
assert not (R/'evidence/compiler-receipt.json').exists(),'One compiler invocation only'
with (R/'evidence'/dispatch).open('x') as f:json.dump(dict(remote_root='/srv/android/asus-linux49-runnable-timer-format-fix-20261107-bee07d4f',remote_py=str(rp),remote_py_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),attempt=1,transport_dispatch=1,vm_lifecycle_operations=False),f,indent=2)
result=json.loads(remote.run(script))
for n,v in result.items():
 data=base64.b64decode(v)
 if n=='source/init.c':assert data==source
 else:(R/n).write_bytes(data)
(R/'artifacts/init').chmod(0o755)
print((R/'evidence/compiler-receipt.json').read_text())
