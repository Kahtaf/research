from pathlib import Path
import base64,gzip,hashlib,json,subprocess
from vm import R,channel
I=json.loads((R/'evidence/identity.json').read_text())
script=r'''from pathlib import Path
import base64,gzip,hashlib,json,subprocess
R=Path(ROOT);O=R/'out';E=R/'evidence'
s=json.loads((E/'build-status.json').read_text());b=json.loads((E/'build-receipt.json').read_text())
assert s['kernel_builds']==1 and s['helper_compiles']==0 and s['error'].startswith('FileNotFoundError')
assert b['kernel_builds']==1 and b['config_byte_identical'] and b['compiled_DT_byte_identical']
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
syms={l.split()[-1]:[int(l.split()[0],16),int(l.split()[1],16)] for l in nm.splitlines() if len(l.split())==4}
start,size=syms['kmsg_fops']
cmd=['aarch64-linux-gnu-objdump','-s','--start-address='+hex(start),'--stop-address='+hex(start+size),str(O/'vmlinux')]
(E/'linked-kmsg-fops.txt').write_text(subprocess.check_output(cmd,text=True))
(E/'linked-route-symbols.json').write_text(json.dumps({n:dict(address=hex(syms[n][0]),size=syms[n][1]) for n in ['kmsg_fops','devkmsg_write','asus_devkmsg_boundary','log_store','asus_retained_trace_write','vprintk_emit','printk_emit','memory_open','__vfs_write']},indent=2)+'\n')
(E/'qualification-recovery.json').write_text(json.dumps(dict(kernel_build_completed=True,only_failure='post-build cross-GDB unavailable',original_status_preserved=True,recovery='read-only nm/objdump linked kmsg_fops pointer inspection',command=cmd,extra_kernel_builds=0),indent=2)+'\n')
files={}
for p in E.iterdir():
 if p.is_file():
  assert p.stat().st_size<2*1024**2,(p.name,p.stat().st_size)
  files['evidence/'+p.name]=p.read_bytes()
files['artifacts/Image.gz-dtb']=(O/'arch/arm64/boot/Image.gz-dtb').read_bytes()
files['artifacts/resolved.config']=(O/'.config').read_bytes()
m=(O/'System.map').read_bytes();files['artifacts/System.map.gz']=gzip.compress(m,compresslevel=9,mtime=0)
files['evidence/System.map-uncompressed.json']=(json.dumps(dict(bytes=len(m),sha256=hashlib.sha256(m).hexdigest()),indent=2)+'\n').encode()
print(json.dumps({n:base64.b64encode(d).decode() for n,d in files.items()}))
'''.replace('ROOT',repr(I['remote_root']))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);assert not p.returncode,p.stderr
pins={}
for n,data in json.loads(p.stdout).items():
 d=base64.b64decode(data);path=R/n
 # Existing identical identity/prepost stay identical; no source overwrite.
 if path.exists():assert path.read_bytes()==d,n
 else:path.write_bytes(d)
 pins[n]=dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest())
(R/'evidence/fetch-receipt.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(dict(build=json.loads((R/'evidence/build-receipt.json').read_text()),map=json.loads((R/'evidence/System.map-uncompressed.json').read_text())),indent=2))
