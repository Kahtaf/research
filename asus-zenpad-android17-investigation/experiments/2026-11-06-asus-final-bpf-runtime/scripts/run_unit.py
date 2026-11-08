from pathlib import Path
import os,resource,json,hashlib,subprocess as s,gzip,stat,struct,time
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-bpf-runtime-20261106');N=Path('/srv/android/asus-network-runtime');P=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');C=O/'capture/root';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (O/'evidence/capture.json').exists()
assert sha(N/'handoff-r1/Image')=='f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6'
assert sha(N/'handoff-r1/network.config')=='8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01'
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(O/'scripts/fixture_init.c'),'-o',str(O/'fixture-init')];p=s.run(cmd,capture_output=True,text=True);(O/'evidence/fixture-compile.json').write_text(json.dumps(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0
# Retain the immutable qualified dynamic runtime dependencies, with every byte pinned.
base=P/'inputs/runtime-root-r2';files={str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file() and (('/lib64/' in str(p)) or p.name in ['linker64','toybox','property_info'])}
for p in C.rglob('*'):
 if p.is_file():files[str(p.relative_to(C))]=p.read_bytes()
files['apex/com.android.uprobestats/bin/uprobestatsbpfload']=(O/'capture/com.android.uprobestats-selected-apex/bin/uprobestatsbpfload').read_bytes()
for name in ['loader_probe','handler_probe','policy_probe','network_probe']:files['system/bin/'+name]=(N/'artifacts'/name).read_bytes()
# Exact ELF section bytes: no code rewrite, relocation or substitute object.
b=(C/'system/vendor/etc/bpf/filterPowerSupplyEvents.o').read_bytes();off=struct.unpack_from('<Q',b,40)[0];ents,num,idx=struct.unpack_from('<HHH',b,58);sects=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*ents) for i in range(num)];strings=b[sects[idx][4]:sects[idx][4]+sects[idx][5]]
for sec in sects:
 name=strings[sec[0]:].split(b'\0',1)[0].decode()
 if name in ['skfilter/power_supply','license']:
  files['vendor-insns' if name.startswith('skfilter') else 'vendor-license']=b[sec[4]:sec[4]+sec[5]]
files['init']=(O/'fixture-init').read_bytes();files['entropy.seed']=os.urandom(64)
# No seed_properties executable or readiness setter enters this initrd.
assert not any('seed_properties' in n for n in files)
for mode in ['actual','mandatory-malformed']:
 R=O/('run-'+mode);R.mkdir();f=dict(files)
 if mode=='mandatory-malformed':f['apex/com.android.tethering/etc/bpf/mainline/netd.o']=b'FINAL_BYTE_MALFORMED_NOT_ELF\n'
 archive=bytearray()
 def entry(name,mode,data=b'',major=0,minor=0):
  n=name.encode()+b'\0';vals=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];archive.extend(b'070701'+''.join(f'{v:08x}' for v in vals).encode()+n);archive.extend(b'\0'*(-len(archive)%4));archive.extend(data);archive.extend(b'\0'*(-len(archive)%4))
 dirs={'dev','proc','sys','tmp','data','linkerconfig','mnt','system/vendor/etc/bpf'}
 for n in f:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
 for d in sorted(dirs,key=lambda x:(x.count('/'),x)):entry(d,stat.S_IFDIR|0o755)
 entry('vendor',stat.S_IFLNK|0o777,b'/system/vendor');entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
 for n,data in sorted(f.items()):entry(n,stat.S_IFREG|(0o755 if n=='init' or '/bin/' in n else 0o644),data)
 entry('TRAILER!!!',0);(R/'initramfs.cpio.gz').write_bytes(gzip.compress(archive,mtime=0));del archive
 (R/'inputs.json').write_text(json.dumps({n:hashlib.sha256(data).hexdigest() for n,data in f.items()},indent=2))
 cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-accel','tcg,thread=single,tb-size=16','-cpu','cortex-a53','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(N/'handoff-r1/Image'),'-initrd',str(R/'initramfs.cpio.gz'),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=6 printk.devkmsg=on']
 (R/'command.json').write_text(json.dumps(dict(argv=cmd,timeout_seconds=120,rlimit_as_bytes=1024**3,cpu_affinity=list(os.sched_getaffinity(0)),initramfs_sha256=sha(R/'initramfs.cpio.gz'),started=time.time()),indent=2))
 with (R/'serial.log').open('w') as log:
  try:p=s.run(['/usr/bin/time','-v','-o',str(R/'host-resources.txt'),*cmd],stdin=s.DEVNULL,stdout=log,stderr=s.STDOUT,timeout=120);code=p.returncode;timeout=False
  except s.TimeoutExpired:code=None;timeout=True
 text=(R/'serial.log').read_text(errors='replace');result=dict(qemu_exit=code,timeout=timeout,complete='FINAL_BYTE_FIXTURE_DONE' in text,log_sha256=sha(R/'serial.log'),mode=mode);(R/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);print('\n'.join(x for x in text.splitlines() if any(v in x for v in ['EXEC_RESULT','VENDOR_','FINAL_BYTE','CANNOT LINK','FATAL','assert','fatal'])),flush=True)
print('ALLOCATION_BYTES',sum(p.stat().st_blocks*512 for p in O.rglob('*') if p.is_file()))
