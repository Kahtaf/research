"""One serial static ARM64 build and package; no kernel/platform build or sweeps."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,struct,gzip
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]
assert str(R)=='/srv/android/asus-linux49-microsd-report-20261107'
os.chdir(R)
os.environ.update(LC_ALL='C',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(R/'source'))
import bootformat as b
from package_probe import package
from lk_contract import HEADER
H=lambda x:hashlib.sha256(x).hexdigest()
logs=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr or p.stdout)
 return p.stdout
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']
run(['gcc',*flags,'-Wno-unused-function','source/test_init.c','-o','artifacts/test_init'])
print(run(['artifacts/test_init']))
# Exactly one serial cross compiler invocation; no resource settings for other processes.
run(['aarch64-linux-gnu-gcc','-static',*flags,'-Wl,--build-id=none','-fno-ident','source/init.c','-o','artifacts/init'])
init=(R/'artifacts/init').read_bytes();elf=b.elf_static(init)
k=Path('/srv/android/asus-bmc156-full-kernel-r1/out/arch/arm64/boot/Image.gz-dtb').read_bytes()
im,cp,gz,contract=package(init,k,(R/'inputs/original-header').read_bytes(),(R/'inputs/original-kernel-wrapper').read_bytes(),(R/'inputs/original-wrapper').read_bytes())
(R/'artifacts/candidate.img').write_bytes(im)
padded=im+bytes(b.PARTITION_SIZE-len(im));(R/'artifacts/candidate.p10.raw').write_bytes(padded)
# One small package-layout check of the actual candidate.
h,kw,rw,tail=b.parse_image(im)
rawcp,extra=b.ungzip(rw[512:]);entries=b.parse_cpio(rawcp)
assert not tail and not extra and rawcp==cp and set(entries)=={'init','dev','proc','sys','sd'}
assert entries['init']==(0o100755,0,0,init) and gzip.decompress(gz)==cp
assert h[64:576].split(b'\0')[0]==HEADER
assert struct.unpack_from('<I',h,16)[0]==len(rw) and contract['compressed_Image_unchanged']
run_id=(R/'inputs/run-id.txt').read_text().strip();assert run_id.encode() in init
manifest=dict(status='OFFLINE_CANDIDATE_NO_PHYSICAL_TEST',run_id=run_id,marker={'name':'PROBE.ID','exact_ascii_contents':run_id+'\n'},report='PROBE.TXT',image={'bytes':len(im),'sha256':H(im)},p10={'bytes':len(padded),'sha256':H(padded),'path':str(R/'artifacts/candidate.p10.raw')},init={'bytes':len(init),'sha256':H(init),**elf},packaging=contract,checks=['three focused mock behavior groups','actual candidate layout and static ELF'],build={'ARM64_static_compiler_invocations':1,'parallel_jobs':1},physical_boot_verified=False,sd_hardware_verified=False,automatic_return_proven=False)
(R/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
