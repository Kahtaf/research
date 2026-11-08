from pathlib import Path
import os,resource,subprocess,json,hashlib,sys,gzip,shutil
R=Path(__file__).resolve().parents[1];assert str(R)=='/srv/android/asus-minimal-ram-usb-probe-20261106';os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1793923200',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
H=lambda b:hashlib.sha256(b).hexdigest();logs=[];peak=0

def usage():
 global peak
 n=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());peak=max(peak,n);assert n<=256*1024**2;return n

def run(cmd,timeout=60):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,timeout=timeout)
 logs.append({'command':[str(x) for x in cmd],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n');usage()
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout

sys.path.insert(0,str(R/'source'));import bootformat as b
pins=json.loads((R/'inputs/stock-input-pins.json').read_text());old=Path('/srv/android/2026-11-06-asus-stock-only-ram-rescue-build/artifacts')
k=(old/'base-kernel').read_bytes();assert H(k)==pins['base-kernel']['sha256'];h=(R/'inputs/original-header').read_bytes();w=(R/'inputs/original-wrapper').read_bytes();assert H(h)==pins['original-header']['sha256'] and H(w)==pins['original-wrapper']['sha256']
# Pin the exact existing compiler, linker, assembler, startup objects and static libraries.
tools={}
for compiler in ['gcc','aarch64-linux-gnu-gcc']:
 for p in [Path(shutil.which(compiler))]+[Path(run([compiler,('-print-prog-name=' if n in ['cc1','collect2'] else '-print-file-name=')+n]).strip()) for n in ['cc1','collect2','crt1.o','crti.o','crtn.o','crtbeginT.o','crtend.o','libc.a','libgcc.a','libgcc_eh.a']]:
  assert p.is_file(),str(p);tools[str(p)]={'sha256':H(p.read_bytes()),'bytes':p.stat().st_size}
for name in ['ld','as','aarch64-linux-gnu-ld','aarch64-linux-gnu-as','aarch64-linux-gnu-objdump','aarch64-linux-gnu-readelf','fsck.fat','python3']:
 p=Path(shutil.which(name));tools[str(p)]={'sha256':H(p.read_bytes()),'bytes':p.stat().st_size}
(R/'evidence/toolchain-pins.json').write_text(json.dumps(tools,indent=2)+'\n')
flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wl,--build-id=none','-fno-ident']
for name in ['init','init-reproduction']:run(['aarch64-linux-gnu-gcc',*flags,'source/init.c','-o','artifacts/'+name],120)
assert (R/'artifacts/init').read_bytes()==(R/'artifacts/init-reproduction').read_bytes();b.elf_static((R/'artifacts/init').read_bytes())
run(['aarch64-linux-gnu-readelf','-h','-l','artifacts/init'])
run(['gcc',*flags,'-Wno-unused-function','source/test_init.c','-o','artifacts/test_init'],120)
run(['artifacts/test_init'])
run(['fsck.fat','-n','-v','artifacts/report-fixture.fat'])

def package(init_name):
 entries={n:(0o40755,0,0,b'') for n in ['dev','proc','sys']};entries['init']=(0o100755,0,0,(R/'artifacts'/init_name).read_bytes())
 cp=b.make_cpio(entries);assert b.parse_cpio(cp)==entries
 gz=bytearray(gzip.compress(cp,compresslevel=9,mtime=0));gz[9]=255;gz=bytes(gz)
 im=b.make_image(h,k,b.wrap(w,gz));return im,cp,gz
im,cp,gz=package('init');im2,cp2,gz2=package('init-reproduction');assert (im,cp,gz)==(im2,cp2,gz2)
(R/'artifacts/candidate.img').write_bytes(im);(R/'artifacts/candidate.p10.raw').write_bytes(im+bytes(b.PARTITION_SIZE-len(im)));(R/'artifacts/initramfs.cpio.gz').write_bytes(gz)
run(['python3','-B','scripts/verify.py'])
run(['python3','-B','scripts/kernel_api.py'])
for p in sorted((R/'extracted/kernel-functions').glob('*.elf')):
 (R/'evidence'/('stock-'+p.stem+'.disasm')).write_text(run(['aarch64-linux-gnu-objdump','-d',p]))
for p,pin in tools.items():assert H(Path(p).read_bytes())==pin['sha256']
assert H((old/'base-kernel').read_bytes())==pins['base-kernel']['sha256']
owned=usage();(R/'evidence/resources.json').write_text(json.dumps({'cpu_affinity':sorted(os.sched_getaffinity(0)),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_cpu':resource.getrlimit(resource.RLIMIT_CPU),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'owned_bytes':owned,'observed_peak_bytes':peak,'max_owned_bytes':256*1024**2,'subprocess_timeout_seconds_max':120,'parallelism':1,'device_operations':0},indent=2)+'\n')
manifest={'status':'OFFLINE_CANDIDATE_NO_PHYSICAL_TEST','run_id':'b8bfa53e-4142-4ec8-b603-8f25cb617e2e','image':{'bytes':len(im),'sha256':H(im)},'p10':{'bytes':16740352,'sha256':H(im+bytes(16740352-len(im)))},'wrapped_kernel_sha256':H(k),'init_sha256':H((R/'artifacts/init').read_bytes()),'gzip_sha256':H(gz),'reproduction':{'ELF_byte_identical':True,'gzip_newc_byte_identical':True,'image_byte_identical':True},'allowed_parent_transition_preimages':['3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a','902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'],'source_pins':{str(p.relative_to(R)):H(p.read_bytes()) for group in ['source','scripts','inputs'] for p in sorted((R/group).rglob('*')) if p.is_file()},'physical_validation':False,'automatic_return_proven':False,'persistent_write_scope':[]}
(R/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2));print('OFFLINE_MINIMAL_PROBE_PASS')
