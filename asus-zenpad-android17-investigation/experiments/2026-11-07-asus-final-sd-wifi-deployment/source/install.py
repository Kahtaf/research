#!/usr/bin/env python3
"""Deploy only an actual final SD-rescue assembly to fixed p10; default PLAN_ONLY."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,socket,sys,time,uuid
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
def sha(data): return hashlib.sha256(data).hexdigest()
FROZEN_PINS={
 "2026-11-07-asus-wifi-microsd-probe/source/install.py": "58947caace8dfbc2d5140d77f3a657883d41caca4bf1c35fc81eda185ecc480e",
 "2026-11-07-asus-wifi-microsd-probe/source/adb": "820fd0d66e75ee98701798e385f04e48a026ec7abd22ec6a67e9760ed0829e82",
 "2026-11-07-asus-wifi-microsd-probe/source/legacy_adb.py": "6d00836d7e0cc28834f858b0fd6ab5515ffe7b3ecd37a6da6ba1f66b43597731",
 "2026-11-07-asus-wifi-recovery-probe/scripts/install.py": "37c8071e74dd6e6666e34e53a00fc9353ee2cc20c6b3c81bb28ccc6e50467603",
 "2026-11-06-asus-linux49-minimal-probe-transition/source/adapter.py": "e134cf83c21e99261c9df5a844c496888cc26e68fbc5baf6be7b4835f675f26b",
 "2026-11-06-asus-linux49-minimal-probe-transition/source/engine.py": "630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681",
 "2026-11-06-asus-linux49-minimal-probe-transition/source/root_dispatch.py": "38c8030193f32084b6549bf81f6e1d2f9428fb516a6853295eb1adb4208407bc",
 "2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py": "684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34"
}
def check_frozen():
 for relative,pin in FROZEN_PINS.items():
  if sha((WORK/relative).read_bytes())!=pin: raise ValueError('Frozen Wi-Fi dependency changed: '+relative)
check_frozen()
WIFI=WORK/'2026-11-07-asus-wifi-recovery-probe/scripts/install.py'
WIFI_SHA='37c8071e74dd6e6666e34e53a00fc9353ee2cc20c6b3c81bb28ccc6e50467603'
spec=importlib.util.spec_from_file_location('preserved_wifi_transport',WIFI)
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
a,b=w.a,w.b
require=b.require
ADMISSION=ROOT/'source/admission.py'
ADMISSION_SHA='ef16e88edb9e4a4e7c0deccdc318b4a23f1ab8ee4b8880c440bd4c58c527e599'
require(sha(ADMISSION.read_bytes())==ADMISSION_SHA,'Final assembly admission source changed')
spec=importlib.util.spec_from_file_location('final_sd_admission',ADMISSION)
admission=importlib.util.module_from_spec(spec);spec.loader.exec_module(admission)
IMAGE_SHA=FULL_SHA=None
ASSEMBLY={}
INSTALL_PREIMAGES=(b.STOCK_HASH,'78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9')
SELF=Path(__file__)
SELF_SHA=sha(SELF.read_bytes())
SHIM_DIR=WORK/'2026-11-07-asus-wifi-microsd-probe/source'
LEGACY_PINS={WORK/p:h for p,h in FROZEN_PINS.items() if p.endswith(('/adb','/legacy_adb.py'))}
class Guard(w.Guard):
 def check(self):
  super().check()
  require(sha(SELF.read_bytes())==SELF_SHA and sha(WIFI.read_bytes())==WIFI_SHA,'Final SD deployment driver changed')
  require(all(sha(p.read_bytes())==h for p,h in LEGACY_PINS.items()),'Legacy shell adapter changed')
  check_frozen();admission.check_sources()
  require(sha(ADMISSION.read_bytes())==ADMISSION_SHA,'Final assembly admission changed')
  require(sha(admission.ordinary(Path(ASSEMBLY['assembly_directory'])/'assembly.json',65536))==ASSEMBLY['assembly_sha256'],'Admitted assembly receipt changed')
class Journal(b.Journal):
 def __init__(self,directory,run):
  self.directory=directory
  self.state=dict(schema=1,mode='EXECUTE',run_id=run,profile='exact-final-offline-sd-rescue',assembly=ASSEMBLY,
   candidate_sha256=IMAGE_SHA,full_p10_sha256=FULL_SHA,target=b.BLOCK,
   events=[],write_dispatches=[],outcome='preparing',partition_status='not_observed',
   restore_verified=False,cleanup='not_attempted',physical_kernel_boot_proven=False,
   transport='authenticated-adb-tcp',endpoint=b.ENDPOINT,reboot=False)
  self.save()
 def save(self):
  try: a.durable(self.directory/'state.json',self.state)
  except (OSError,ValueError) as e: raise b.UncertainTransport('Cannot persist current operation state') from e
 def observed(self,data):
  h=sha(data)
  self.state.update(partition_status='exact_candidate' if h==FULL_SHA else 'exact_stock' if h==b.STOCK_HASH else 'known_previous' if h in INSTALL_PREIMAGES else 'unexpected_bytes',partition_may_be_modified=h!=b.STOCK_HASH)
  self.save()
class Transport(w.WifiTransport):
 def adb(self,args,timeout=60):
  if args and args[0]=='shell':args=['shell','-T',*args[1:]]
  return super().adb(args,timeout)
 def command(self,argv,*,script=None,timeout=90):
  try:return super().command(argv,script=script,timeout=timeout)
  except UnicodeError as exc:
   self.guard.stopped=True
   raise b.UncertainTransport('Undecodable command completion; no automatic inverse or further commands') from exc
 def healthy(self):
  super().healthy()
  require(self.adb(['shell','getprop','init.svc.flash_recovery'])=='stopped','Stock recovery restoration still active or unrecognized')
def inputs(directory):
 global IMAGE_SHA,FULL_SHA,ASSEMBLY
 full,ASSEMBLY=admission.admit(directory)
 a.check_sources()
 IMAGE_SHA=ASSEMBLY['candidate_sha256'];FULL_SHA=ASSEMBLY['full_p10_sha256']
 stock,_=b.local_inputs()
 return stock,full

def execute(action, stock, candidate, t, j):
    """Only a known candidate completion failure can enter the single bounded inverse."""
    def verified_stock():
        data = t.read()
        if len(data) != b.SIZE or sha(data) != b.STOCK_HASH:
            raise b.VerificationFailed('Full stock inverse readback mismatch')
        t.healthy()
        j.state['restore_verified'] = True
        j.save()

    try:
        t.healthy()
        t.setup()
        t.stage('stock', stock)
        if action == 'install':
            t.stage('candidate', candidate)
        before = t.read()
        if action == 'install':
            require(len(before) == b.SIZE and sha(before) in INSTALL_PREIMAGES,
                    'Install requires one exact complete allowed physical p10 preimage')
            j.state.update(install_preimage_sha256=sha(before), install_preimage_bytes=len(before))
            j.save()
            t.healthy()
            t.write('candidate')
            data = t.read()
            if len(data) != b.SIZE or sha(data) != FULL_SHA:
                raise b.VerificationFailed('Full installed candidate readback mismatch')
            t.healthy()
            outcome = 'installed_full_hash_verified'
        else:
            # Never replace arbitrary unexpected recovery bytes in a later restore phase.
            require(sha(before) in (FULL_SHA, b.STOCK_HASH), 'Unexpected recovery hash; restore refused')
            t.healthy()
            if sha(before) == b.STOCK_HASH:
                j.state['restore_verified'] = True
                outcome = 'verified_already_original'
            else:
                t.write('stock')
                verified_stock()
                outcome = 'restored_full_hash_verified'
    except b.UncertainTransport as exc:
        t.guard.stopped = True
        return j.finish('terminal_uncertainty_no_commands', error=str(exc))
    except (b.Refused, b.OperationFailed, b.VerificationFailed, OSError, ValueError) as exc:
        candidate_sent = [x['source'] for x in j.state['write_dispatches']] == ['candidate']
        if action != 'install' or not candidate_sent:
            return j.finish('refused_or_failed_stop', error=str(exc))
        try:
            t.guard.check()
            t.healthy()
            current = t.read()
            if sha(current) == b.STOCK_HASH:
                j.state['restore_verified'] = True
                outcome = 'install_failed_already_original_verified'
            else:
                t.write('stock')
                verified_stock()
                outcome = 'install_failed_fixed_inverse_verified'
        except (b.Refused, b.OperationFailed, b.VerificationFailed, b.UncertainTransport, OSError, ValueError) as inverse:
            t.guard.stopped = True
            return j.finish('inverse_unverified_stop', error=str(exc), inverse_error=str(inverse))
    # Only a valid, known complete phase may attempt cleanup, never after uncertainty/expiry.
    try:
        t.guard.check()
        t.cleanup()
        t.healthy()
        return j.finish(outcome, cleanup='verified')
    except (b.Refused, b.OperationFailed, b.VerificationFailed, b.UncertainTransport, OSError, ValueError) as exc:
        t.guard.stopped = True
        return j.finish(outcome, cleanup='unverified', cleanup_error=str(exc))

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--assembly-dir',type=Path,default=admission.DEFAULT_ASSEMBLY)
 parser.add_argument('--execute',action='store_true')
 args=parser.parse_args()
 try:stock,candidate=inputs(args.assembly_dir)
 except (b.Refused,ValueError,AssertionError,KeyError,TypeError,OSError,UnicodeError) as exc:
  print(json.dumps(dict(mode='EXECUTE' if args.execute else 'PLAN_ONLY',outcome='refused',error=str(exc),device_contacted=False,reboot=False)),file=sys.stderr)
  return 2
 if not args.execute:
  print(json.dumps(dict(mode='PLAN_ONLY',candidate_sha256=IMAGE_SHA,full_p10_sha256=FULL_SHA,endpoint=b.ENDPOINT,target=b.BLOCK,assembly=ASSEMBLY,allowed_preimages=list(INSTALL_PREIMAGES),device_contacted=False,reboot=False)))
  return 0
 os.umask(0o077)
 for key in list(os.environ):
  if key.startswith(('ADB_','ANDROID_ADB_')) or key=='ANDROID_SERIAL':del os.environ[key]
 os.environ['PATH']=str(SHIM_DIR)+os.pathsep+'/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools'+os.pathsep+os.environ.get('PATH','/usr/bin:/bin')
 with socket.create_connection(('127.0.0.1',5037),timeout=2) as server:
  server.sendall(b'000chost:version');require(server.recv(64).startswith(b'OKAY'),'Existing ADB server required')
 run=str(uuid.uuid4());directory=ROOT/'private'/run
 directory.mkdir(parents=True,mode=0o700)
 guard=Guard(a.code_receipt()['sha256'])
 with a.mutation_lock():
  j=Journal(directory,run);t=Transport(directory,j,guard,run)
  state=execute('install',stock,candidate,t,j)
  if state['outcome']=='refused_or_failed_stop' and not state['write_dispatches'] and state['partition_status']=='exact_candidate' and not guard.stopped:
   guard.check();t.healthy();t.cleanup();t.healthy()
   state=j.finish('verified_already_candidate',cleanup='verified')
 result=dict(outcome=state['outcome'],run_id=run,cleanup=state['cleanup'],writes=len(state['write_dispatches']),full_p10_sha256=FULL_SHA,reboot=False,physical_boot_proven=False)
 a.durable(ROOT/'evidence'/(run+'.json'),result)
 print(json.dumps(result),flush=True)
 return 0 if result['outcome'] in ('installed_full_hash_verified','verified_already_candidate') and result['cleanup']=='verified' else 2
if __name__=='__main__':raise SystemExit(main())
