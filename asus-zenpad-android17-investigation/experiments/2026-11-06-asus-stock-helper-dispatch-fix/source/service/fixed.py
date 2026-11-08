"""Immutable stock-only scope. No device operations at import or in plan mode."""
from __future__ import annotations
import hashlib,importlib.util,json,os,re,sys,types
from pathlib import Path
S=Path(__file__).resolve().parents[2];W=S.parent
PRIOR=W/'2026-11-06-asus-stock-programmatic-control'
ENGINE=W/'2026-11-06-asus-recovery-control-wifi/source/recovery_control.py'
ENGINE_SHA='34ed0079e7f9ca3b4edcab5d108fe29d330a653781c4ec5d67b8ca421daac0ab'
PROFILE='asus-stock-only-init-mediated-v2'
CANDIDATE=W/'2026-11-06-asus-android17-os-rescue/artifacts/candidate-final/UNTESTED-stock-control.img'
IMAGE_SHA='7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5'
FULL_SHA='6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925'
KERNEL_SHA='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
STOCK_SHA='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
SIZE=16740352
PARA_SHA='8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef'
PARA_SIZE=524288
INIT_SHA='e9594c0d1cbe7d05d34acd63e90b424672360ceb09112fa16b5b23390c21b7e5'
ADBD_SHA='78a7adbda0a28da4055da1ea68a2ead8ee01764a365778930ef03e6649dcb450'
SERIAL='DEVICE_SERIAL_REDACTED';DIAG_SERIAL='0123456789ABCDEF';ENDPOINT='IP_REDACTED:5555'
FINGERPRINT='asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'
KERNEL_BANNER='Linux version 3.18.35 (android@mec15) (gcc version 4.9 20150123 (prerelease) (GCC) ) #1 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018'
MARKER='ASUS RAM-only diagnostic os-rescue-v1'
STOCK_ROW={'serial':SERIAL,'state':'device','product':'WW_P00A','model':'P00A','device':'P00A_2'}
DIAG_ROW={'serial':DIAG_SERIAL,'state':'recovery','product':'p00a_diagnostic','model':'P00A_RAM_diagnostic','device':'p00a'}
STOCK_PROPS={'ro.serialno':SERIAL,'ro.product.device':'P00A_2','ro.product.name':'WW_P00A','ro.product.model':'P00A',
 'ro.build.version.sdk':'24','ro.build.fingerprint':FINGERPRINT,'sys.boot_completed':'1','ro.adb.secure':'1'}
AUTH=PRIOR/'evidence/service/user-authorization-record.json'
ACCEPTANCE=W/'2026-11-06-asus-android17-orchestration/evidence/stock-os-backup-parent-acceptance.json'
ACCEPTANCE_SHA='73f979aa1a74766fdd485960c04e64da716aad37650dc45b2c4f858e9b19841f'
class Refused(Exception):pass
class Unknown(Exception):pass

def require(ok,message):
 if not ok:raise Refused(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path,limit=SIZE):
 require(path.is_file() and not path.is_symlink(),'Expected nonsymlink file: '+str(path))
 with path.open('rb') as f:data=f.read(limit+1)
 require(len(data)<=limit,'Input too large: '+str(path));return data

def load_engine():
 source=read(ENGINE);require(sha(source)==ENGINE_SHA,'Pinned writer engine changed')
 module=types.ModuleType('stock_p10_frozen_engine');module.__file__=str(ENGINE)
 # Compile exactly the bytes hashed above; no import-time file reread or old-spike pycache.
 exec(compile(source,str(ENGINE),'exec'),module.__dict__)
 return module
E=load_engine()
# Share the engine's failure taxonomy so its guarded inverse handles every
# completed guard failure, and transport uncertainty always stops the engine.
Refused=E.Refused
Unknown=E.UncertainTransport

class AuthorizationExpired(Exception):
 """A new command was refused; this is not transport uncertainty or an inverse trigger."""

def unique_json(data):
 def pairs(items):
  d={}
  for k,v in items:
   require(k not in d,'Duplicate JSON key '+k);d[k]=v
  return d
 return json.loads(data,object_pairs_hook=pairs)

def fixed_inputs():
 stock,records=E.local_inputs();image=read(CANDIDATE)
 require(len(image)==8654848 and sha(image)==IMAGE_SHA,'Only the fixed repaired stock diagnostic is accepted')
 p,o=E.unpack_image(image),E.unpack_image(stock)
 require(len(image)==p['end'],'Candidate trailer/layout changed')
 require(p['kernel']==o['kernel'] and sha(p['kernel'])==KERNEL_SHA,'Exact stock kernel required')
 require(all(p['header'][i]==o['header'][i] for i in (0,1,3,4,5,6,7,8,9)),'Stock image layout changed')
 require(sha(image[:2048])=='7df0478da8a7a0931296ee2dae1c8bdb2d745259b75ef8f57bb9bf98ed86fd3f','Header changed')
 full=image+bytes(SIZE-len(image));require(sha(full)==FULL_SHA,'Full candidate changed')
 for label in ('initial','verify'):
  p=W/f'2026-11-05-asus-boot-access-audit/artifacts/device-backup/{label}/para.bin';data=read(p)
  require(len(data)==PARA_SIZE and sha(data)==PARA_SHA,'Known-good normal para backup changed')
 require(sha(read(ENGINE))==ENGINE_SHA,'Writer source changed')
 a=read(ACCEPTANCE,65536);require(sha(a)==ACCEPTANCE_SHA,'Parent backup acceptance record changed')
 acceptance=unique_json(a)
 require(acceptance['system_sha256']=='4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'
  and acceptance['system_bytes']==3753902080 and acceptance['backup_exit_code']==acceptance['verify_exit_code']==0
  and acceptance['whole_oem_canonical_match'] is True,'Parent backup acceptance missing')
 return stock,full,records

def fsync_dir(path):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def durable(path,value,exclusive=False):
 data=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if exclusive:
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 else:
  tmp=path.with_name(path.name+'.pending')
  fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 fsync_dir(path.parent)

def valid_run(run):require(isinstance(run,str) and re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[0-9a-f]{16}',run),'Invalid run id');return run
