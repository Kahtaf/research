import os,resource,pathlib,json,hashlib,subprocess,stat,gzip,time,signal,base64,struct,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/asus-r9-actual-system-mount-20261106');O=R/'run';O.mkdir();(O/'tmp').mkdir();I=P('/srv/android/asus-full-system-observer-preparation-20261106/immutable');raw=P('/srv/android/asus-r9-postbuild-validation-r2/validation/system-partition.raw')
PAYLOAD_PLACEHOLDER
SOURCE_MAP_PLACEHOLDER
GATE_PLACEHOLDER
identity=lambda s:dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=oct(stat.S_IMODE(s.st_mode)))
def sha(p):
 h=hashlib.sha256()
 with P(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
fd=os.open(raw,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);before=identity(os.fstat(fd));inspection=json.loads((R/'inspection.json').read_text());assert before==inspection['before']
assert before['bytes']==3753902080 and before['mode']=='0o444'
pins=json.loads((I.parent/'immutable-pins.json').read_text());verified=[]
for row in pins:
 p=I/row['relative'];assert sha(p)==row['sha256'],str(p);verified.append(row)
assert sha(I/'Image')=='c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080'
assert sha(I/'sources/.config')=='0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f'
source_receipt=[]
for rel,want in SOURCE_MAP.items():
 v=P('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source')/rel;p=P('/srv/android/asus-bmc156-full-kernel-r1/kernel')/rel
 vh=sha(v);ph=sha(p);assert vh==ph==want,rel;source_receipt.append(dict(path=rel,virtual=vh,physical=ph))
header=P('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source/fs/ext4/ext4.h').read_text()
assert '#define EXT4_FEATURE_INCOMPAT_SUPP' in header and '#define EXT4_FEATURE_RO_COMPAT_SUPP' in header
for name,data in PAYLOAD.items():(O/name).write_bytes(base64.b64decode(data))
(O/'check_system_header.py').write_text(GATE)
import importlib.util
spec=importlib.util.spec_from_file_location('gate',O/'check_system_header.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
hdr=gate.inspect(str(raw),3753902080)
assert int(hdr['feature_masks']['incompat'],16)&~0x1a3d6==0 and int(hdr['feature_masks']['ro_compat'],16)&~0x277f==0
(O/'verified-inputs.json').write_text(json.dumps(dict(immutable_manifest_sha256=sha(I.parent/'immutable-pins.json'),verified_immutable_count=len(verified),verified_immutable_pins=verified,ext4_source_parity=source_receipt,header=hdr),indent=2))
def bounded():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(I/'lib64'),TMPDIR=str(O/'tmp'),LC_ALL='C',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
def run(cmd,filename,limit=90):
 with (O/filename).open('x')as log:
  log.write(json.dumps(cmd)+'\n');log.flush();return subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=limit,preexec_fn=bounded,env=env).returncode
tc=I/'toolchain'
cc=[str(I/'bin/aarch64-linux-gnu-gcc'),'-B'+str(I/'compiler-bin')+'/', '-nostdinc','-isystem',str(tc/'gcc-include'),'-isystem',str(tc/'include'),'-static','-nostdlib','-fno-use-linker-plugin','-O2','-Wall','-Wextra','-Werror','-MD','-MF',str(O/'headers.d'),str(tc/'lib/crt1.o'),str(tc/'lib/crti.o'),str(tc/'gcc/crtbeginT.o'),str(O/'reader.c'),'-Wl,--start-group',str(tc/'gcc/libgcc.a'),str(tc/'gcc/libgcc_eh.a'),str(tc/'lib/libc.a'),'-Wl,--end-group',str(tc/'gcc/crtend.o'),str(tc/'lib/crtn.o'),'-o',str(O/'init')]
assert run(cc,'compile.log',45)==0,(O/'compile.log').read_text()
with gzip.GzipFile(filename=str(O/'reader.cpio.gz'),mode='wb',compresslevel=1,mtime=0)as out:
 offset=0
 def entry(name,mode,data=b'',major=0,minor=0):
  global offset
  n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0];h=b'070701'+''.join(f'{x:08x}'for x in fields).encode()+n
  out.write(h);offset+=len(h);pad=-offset%4;out.write(bytes(pad));offset+=pad;out.write(data);offset+=len(data);pad=-offset%4;out.write(bytes(pad));offset+=pad
 for n in ['dev','proc','sys','mnt']:entry(n,stat.S_IFDIR|0o755)
 entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1);entry('init',stat.S_IFREG|0o755,(O/'init').read_bytes());entry('TRAILER!!!',0)
cmd=[str(I/'bin/qemu-system-aarch64'),'-machine','virt,gic-version=3','-cpu','cortex-a53','-accel','tcg,thread=single,tb-size=16','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(I/'Image'),'-initrd',str(O/'reader.cpio.gz'),'-blockdev',json.dumps({'driver':'file','filename':str(raw),'node-name':'system-file','read-only':True}),'-blockdev',json.dumps({'driver':'raw','file':'system-file','node-name':'system-raw','read-only':True}),'-device','virtio-blk-device,drive=system-raw','-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=7 selinux=0']
(O/'qemu-argv.json').write_text(json.dumps(cmd,indent=2));start=time.monotonic()
try:rc=run(cmd,'serial.log',75);timed_out=False
except subprocess.TimeoutExpired:rc=None;timed_out=True
serial=(O/'serial.log').read_text(errors='replace');after_mount=identity(os.fstat(fd));assert identity(os.stat(raw,follow_symlinks=False))==before==after_mount
# Exactly one whole-raw hash: post-run, on the same originally opened O_RDONLY fd.
os.lseek(fd,0,os.SEEK_SET);h=hashlib.sha256()
while True:
 b=os.read(fd,1024**2)
 if not b:break
 h.update(b)
after_sha=h.hexdigest();after_hash=identity(os.fstat(fd));os.close(fd)
unchanged=before==after_mount==after_hash==identity(os.stat(raw,follow_symlinks=False))
liblog_match=bool(re.search(r'PATH /system/lib/liblog.so\r?\n.*?READ bytes=\d+ eof=1 sha256=473bb94ce06678bffd72eb2c34d2f105d540cdedba6e5cc9c4f2c2d073449f9d',serial,re.S))
size=sum(p.stat().st_size for p in R.rglob('*')if p.is_file());assert size<=128*1024**2
result=dict(scope='PARENT_ADMITTED_NARROW_ACTUAL_SYSTEM_FS_ONLY',qemu_exit=rc,timed_out=timed_out,elapsed_seconds=time.monotonic()-start,guest_pass='ACTUAL_SYSTEM_MOUNT_RESULT failures=0' in serial,arm32_liblog_expected_sha256_match=liblog_match,header=hdr,before=before,after_mount=after_mount,after_hash=after_hash,identities_unchanged=unchanged,parent_supplied_sha256=inspection['parent_supplied_sha256'],after_sha256=after_sha,full_raw_hash_count=1,source_hash_matches_parent=after_sha==inspection['parent_supplied_sha256'],kernel_sha256=sha(I/'Image'),config_sha256=sha(I/'sources/.config'),retained_inputs_verified_count=len(verified),ext4_source_parity_count=len(source_receipt),generated={n:sha(O/n)for n in ['reader.c','sha256.h','init','reader.cpio.gz','check_system_header.py']},limits=dict(guest_mib=384,guest_vcpus=1,guest_nic=False,host_cpus=1,process_memory_bytes=1024**3,process_cpu_seconds=60,qemu_wall_seconds=75,remote_wall_seconds=90),owned_output_bytes=size,production_image_accepted=False,full_android_runtime_proven=False,physical_GO=False,flash_ready=False,original_r9_overall_exit=1,original_r9_actual_ro_debuggable=0)
result['filesystem_readable_on_virtual_4_9']=rc==0 and not timed_out and result['guest_pass'] and unchanged and result['source_hash_matches_parent'] and liblog_match and not re.search(r'EXT4-fs error|I/O error|Kernel panic',serial,re.I)
(O/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(result=result,serial=serial,compile_log=(O/'compile.log').read_text(),qemu_argv=cmd,verified_inputs=(O/'verified-inputs.json').read_text()),indent=2))
