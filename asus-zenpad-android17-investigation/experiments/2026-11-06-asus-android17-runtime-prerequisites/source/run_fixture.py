from pathlib import Path
import subprocess as s,json,hashlib,os,stat,gzip,re,sys,shutil
from analyze_materials import analyze_materials
R=Path('/srv/android/asus-android17-runtime-prereqs');I=R/'inputs'
name=sys.argv[1];assert re.fullmatch(r'r[0-9]+',name);O=R/('run-'+name);O.mkdir()
os.environ['TMPDIR']=str(O)
for f in ['guest_init.c','binder_probe.cpp','run_fixture.py','analyze_materials.py']:shutil.copyfile(R/'source'/f,O/f)
payloads=json.loads((R/'evidence/payload-manifest.json').read_text())
header='struct payload {const char*name; unsigned long long offset,size,data_size,tree_offset;const char*digest,*salt;int count;const char**files;};\n'
for p in payloads:header+='static const char* '+p['name']+'_files[]={'+','.join(json.dumps(f['path']) for f in p['files'])+'};\n'
header+='static struct payload payloads[]={\n'
for p in payloads:
 v=p['verity'];header+='{'+','.join([json.dumps(p['name']),str(p['offset']),str(p['size']),v['Image Size'],v['Tree Offset'],json.dumps(v['Root Digest']),json.dumps(v['Salt']),str(len(p['files'])),p['name']+'_files'])+'},\n'
header+='};\n';(O/'payloads.h').write_text(header)
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-I'+str(O),str(R/'source/guest_init.c'),'-o',str(O/'init')]
p=s.run(cmd,stdout=s.PIPE,stderr=s.STDOUT,text=True);(O/'compile.txt').write_text(json.dumps(cmd)+'\n'+p.stdout+f'\nexit={p.returncode}\n');print(p.stdout);assert p.returncode==0
files={str(f.relative_to(I/'root')):f.read_bytes() for f in (I/'root').rglob('*') if f.is_file()}
files['init']=(O/'init').read_bytes();files['system/bin/binder-probe']=(R/'artifacts/binder-probe').read_bytes();files['entropy.seed']=os.urandom(64)
archive=bytearray()
def entry(name,mode,data=b'',major=0,minor=0):
 n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0]
 archive.extend(b'070701'+''.join(f'{v:08x}' for v in fields).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
dirs={'dev','proc','sys','tmp','linkerconfig','data','mnt'}
for n in files:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
for d in sorted(dirs,key=lambda n:(n.count('/'),n)):entry(d,stat.S_IFDIR|0o755)
entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
for n,b in sorted(files.items()):entry(n,stat.S_IFREG|(0o755 if n=='init' or '/bin/' in n else 0o400 if n=='entropy.seed' else 0o644),b)
entry('TRAILER!!!',0);(O/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0))
(O/'input-manifest.json').write_text(json.dumps([dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items() if n!='entropy.seed'],indent=2)+'\n')
s.run(['cp','--reflink=auto',str(R/'artifacts/data-base.ext4'),str(O/'data.ext4')],check=True)
k=R/'build-r4/arch/arm64/boot/Image'
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','2','-m','1536','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(k),'-initrd',str(O/'initramfs.cpio.gz'),'-drive',f'file={O}/data.ext4,format=raw,if=none,id=data','-device','virtio-blk-device,drive=data','-append','console=ttyAMA0 earlycon=pl011,0x9000000 rdinit=/init panic=-1 loglevel=7']
(O/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
code=None;timed=False
with (O/'serial.log').open('w') as f:
 try:code=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=300).returncode
 except s.TimeoutExpired:timed=True
text=(O/'serial.log').read_text(errors='replace');hashes=analyze_materials(text,payloads)
m=re.search(r'RUNTIME_PREREQS_RESULT (\{[^\r\n]+\})',text);guest=json.loads(m[1]) if m else None
report=dict(qemu_returncode=code,timed_out=timed,guest=guest,kernel_sha256=hashlib.sha256(k.read_bytes()).hexdigest(),material_hashes=hashes,all_material_hashes_pass=all(h['passed'] for h in hashes),binder_pass='BINDER_MODERN_PASS' in text,corruption_detected='expected_EIO=1' in text,complete='RUNTIME_PREREQS_DONE' in text,physical_hardware_validated=False,full_apex_activation=False)
report['passed']=bool(code==0 and not timed and guest and guest['failures']==0 and report['all_material_hashes_pass'] and report['binder_pass'] and report['corruption_detected'])
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='material_hashes'},indent=2));sys.exit(0 if report['passed'] else 1)
