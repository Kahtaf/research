from pathlib import Path
import os,resource,subprocess,json,hashlib,sys,gzip,shutil
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];assert str(R)=='/srv/android/asus-linux49-minimal-ram-probe-20261106';os.chdir(R)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1793923200',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
H=lambda b:hashlib.sha256(b).hexdigest();logs=[];peak=0

def usage():
 global peak
 n=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());peak=max(peak,n);assert n<=128*1024**2;return n

def run(cmd,timeout=60):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,timeout=timeout)
 logs.append({'command':[str(x) for x in cmd],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n');usage()
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout

sys.path.insert(0,str(R/'source'));import bootformat as b
old=Path('/srv/android/asus-bmc156-full-kernel-r1')
kpath=old/'out/arch/arm64/boot/Image.gz-dtb';k=kpath.read_bytes()
assert len(k)==7716897 and H(k)=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
assert H((old/'out/.config').read_bytes())=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
h=(R/'inputs/original-header').read_bytes();w=(R/'inputs/original-wrapper').read_bytes();kw=(R/'inputs/original-kernel-wrapper').read_bytes()
inputpins={str(p.relative_to(R)):H(p.read_bytes()) for p in (R/'inputs').iterdir() if p.is_file()}
external={str(old/'kernel/drivers/usb/gadget'/n):H((old/'kernel/drivers/usb/gadget'/n).read_bytes()) for n in ['configfs.c','function/f_mass_storage.c','function/storage_common.c']}
external.update({str(old/'out/include/generated'/n):H((old/'out/include/generated'/n).read_bytes()) for n in ['utsrelease.h','compile.h']})
for n,digest in external.items():assert H((R/'inputs'/Path(n).name).read_bytes())==digest
external[str(kpath)]=H(k);external[str(old/'out/.config')]=H((old/'out/.config').read_bytes())
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

from package_probe import package
im,cp,gz,contract=package((R/'artifacts/init').read_bytes(),k,h,kw,w)
im2,cp2,gz2,contract2=package((R/'artifacts/init-reproduction').read_bytes(),k,h,kw,w)
assert (im,cp,gz,contract)==(im2,cp2,gz2,contract2)
(R/'artifacts/candidate.img').write_bytes(im);(R/'artifacts/candidate.p10.raw').write_bytes(im+bytes(b.PARTITION_SIZE-len(im)));(R/'artifacts/initramfs.cpio.gz').write_bytes(gz)
(R/'evidence/packaging-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
run(['python3','-B','scripts/verify.py'])
run(['python3','-B','scripts/source_contract.py'])
for p,pin in tools.items():assert H(Path(p).read_bytes())==pin['sha256']
assert H(kpath.read_bytes())==H(k)
assert {str(p.relative_to(R)):H(p.read_bytes()) for p in (R/'inputs').iterdir() if p.is_file()}==inputpins
for n,digest in external.items():assert H(Path(n).read_bytes())==digest
(R/'evidence/external-input-preservation.json').write_text(json.dumps({'passed':True,'before_after_sha256':external},indent=2)+'\n')
owned=usage();(R/'evidence/resources.json').write_text(json.dumps({'cpu_affinity':sorted(os.sched_getaffinity(0)),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_cpu':resource.getrlimit(resource.RLIMIT_CPU),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'owned_bytes':owned,'observed_peak_bytes':peak,'max_owned_bytes':128*1024**2,'subprocess_timeout_seconds_max':120,'parallelism':1,'device_operations':0},indent=2)+'\n')
manifest={'status':'OFFLINE_CANDIDATE_NO_PHYSICAL_TEST','run_id':'801c68c4-841f-4ea4-9e9e-c608621839ca','image':{'bytes':len(im),'sha256':H(im)},'p10':{'bytes':16740352,'sha256':H(im+bytes(16740352-len(im)))},'compiled_input_kernel_sha256':H(k),'packaging':contract,'init_sha256':H((R/'artifacts/init').read_bytes()),'gzip_sha256':H(gz),'reproduction':{'ELF_byte_identical':True,'gzip_newc_byte_identical':True,'image_byte_identical':True},'source_pins':{str(p.relative_to(R)):H(p.read_bytes()) for group in ['source','scripts','inputs'] for p in sorted((R/group).rglob('*')) if p.is_file() and '__pycache__' not in p.parts},'physical_validation':False,'automatic_return_proven':False,'persistent_write_scope':[]}
(R/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2));print('OFFLINE_MINIMAL_PROBE_PASS')
