"""Serial compact core only, bounded owned fixture, existing compiler and fixed SSH."""
from pathlib import Path
import os,resource,subprocess,json,hashlib,sys,struct
R=Path(__file__).resolve().parents[1]
assert str(R)=='/srv/android/asus-stock-kernel-sd-rescue-20261107'
os.chdir(R);sys.dont_write_bytecode=True
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(95*1024**2,95*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(TMPDIR=str(R/'artifacts'),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',SOURCE_DATE_EPOCH='1794009600')
logs=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'evidence/build-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 print(p.stdout,end='',flush=True)
flags=['-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fno-ident','-Wl,--build-id=none']
for src,name in [('rescue.c','os-rescue'),('supervisor.c','rescue-sd-supervisor'),('sd_frontend.c','rescue-sd'),('p10_restore.c','p10-restore'),('check_runner.c','rescue-sd-check-runner')]:
 run(['aarch64-linux-gnu-gcc','-static',*flags,'source/'+src,'-o','artifacts/'+name])
 print('LINKED '+name,flush=True)
run(['aarch64-linux-gnu-gcc','-static',*flags,'-DSD_CHECK_ONLY','source/sd_frontend.c','-o','artifacts/rescue-sd-check'])
run(['gcc',*flags,'-Isource','tests/sd_binding.c','-o','artifacts/test_sd_binding'])
f=R/'artifacts/sd-fixture';f.mkdir(exist_ok=True)
for name in ['sys/class/block','sys/dev/block','sys/devices/mmc1/card/block/mmcblk1/mmcblk1p1','sys/devices/mmc0/card/block/mmcblk0']:(f/name).mkdir(parents=True,exist_ok=True)
def put(n,s):(f/n).write_text(s+'\n')
def link(n,target):
 if not (f/n).is_symlink():(f/n).symlink_to(f/target)
 assert (f/n).resolve()==(f/target).resolve()
for n,target in [('sys/class/block/mmcblk1','sys/devices/mmc1/card/block/mmcblk1'),('sys/dev/block/179:128','sys/devices/mmc1/card/block/mmcblk1'),('sys/class/block/mmcblk1p1','sys/devices/mmc1/card/block/mmcblk1/mmcblk1p1'),('sys/dev/block/179:129','sys/devices/mmc1/card/block/mmcblk1/mmcblk1p1'),('sys/class/block/mmcblk0','sys/devices/mmc0/card/block/mmcblk0'),('sys/devices/mmc1/card/block/mmcblk1/device','sys/devices/mmc1/card'),('sys/devices/mmc0/card/block/mmcblk0/device','sys/devices/mmc0/card')]:link(n,target)
for n,s in [('sys/class/block/mmcblk1/removable','0'),('sys/class/block/mmcblk1/device/type','SD'),('sys/class/block/mmcblk1/dev','179:128'),('sys/class/block/mmcblk1p1/dev','179:129'),('sys/class/block/mmcblk1p1/partition','1'),('sys/class/block/mmcblk1p1/start','2048'),('sys/class/block/mmcblk1p1/size','31000000'),('sys/class/block/mmcblk1/size','31116288')]:put(n,s)
run(['artifacts/test_sd_binding',str(f),'1'])
put('sys/class/block/mmcblk1/dev','179:32')
run(['artifacts/test_sd_binding',str(f),'0'])
put('sys/class/block/mmcblk1/dev','179:128')
put('sys/class/block/mmcblk1/device/type','MMC')
run(['artifacts/test_sd_binding',str(f),'0'])
run(['gcc',*flags,'-Isource','tests/check_plan.c','-o','artifacts/test_check_plan'])
run(['artifacts/test_check_plan'])
run(['gcc',*flags,'-Isource','tests/check_runner_status.c','-o','artifacts/test_runner_status'])
run(['artifacts/test_runner_status'])
for n,pin in [('sepolicy','e559a17ee13b141ceca868df7311bee2e095cf340afee2fedb549d314b5cad11'),('file_contexts.bin','23b72f009d21abd8222b65b573506d59f6b00228271316ad2fa62a672c26fbad')]:assert hashlib.sha256((R/'artifacts'/n).read_bytes()).hexdigest()==pin
sys.path.insert(0,str(R/'source'));import bootformat as b
elf={}
for name in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore','rescue-sd-check','rescue-sd-check-runner']:
 d=(R/'artifacts'/name).read_bytes();elf[name]=b.elf_static(d);assert struct.unpack_from('<H',d,16)[0]==2
(R/'evidence/elf.json').write_text(json.dumps(elf,indent=2)+'\n')
run(['python3','-B','scripts/assemble_common.py'])
names=['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore','rescue-sd-check','rescue-sd-check-runner','sepolicy','file_contexts.bin','common-rootfs.cpio.gz']
products={n:dict(bytes=(R/'artifacts'/n).stat().st_size,sha256=b.sha((R/'artifacts'/n).read_bytes())) for n in names}
(R/'artifacts/ARTIFACTS.json').write_text(json.dumps(products,indent=2)+'\n')
allocated=sum(p.lstat().st_blocks*512 for p in R.rglob('*'))
assert allocated<96*1024**2
(R/'evidence/resources.json').write_text(json.dumps(dict(owned_fixture=str(R),allocated_bytes=allocated,allocation_limit_bytes=96*1024**2,address_space_limit_bytes=95*1024**2,parallel_jobs=1,cpu_affinity=sorted(os.sched_getaffinity(0)),kernel_platform_build=False),indent=2)+'\n')
print('STOCK_KERNEL_SD_CORE_BUILD_PASS',flush=True)
