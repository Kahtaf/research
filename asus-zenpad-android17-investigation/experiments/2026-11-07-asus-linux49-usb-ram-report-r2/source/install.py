#!/usr/bin/env python3
"""Install only the exact microSD-report recovery probe over authenticated Wi-Fi."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,socket,sys,time,uuid
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
WIFI=WORK/'2026-11-07-asus-wifi-recovery-probe/scripts/install.py'
WIFI_SHA='37c8071e74dd6e6666e34e53a00fc9353ee2cc20c6b3c81bb28ccc6e50467603'
def sha(data): return hashlib.sha256(data).hexdigest()
if sha(WIFI.read_bytes())!=WIFI_SHA: raise SystemExit('Wi-Fi transport source changed')
spec=importlib.util.spec_from_file_location('preserved_wifi_transport',WIFI)
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
a,b=w.a,w.b
require=b.require
IMAGE=ROOT/'artifacts/candidate.img'
IMAGE_SHA='291b824fca69544253ea55ad91e1edf95d0d651dd8c5400c999a8d946c3dc915'
FULL_SHA='5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453'
INSTALL_PREIMAGES=(*a.INSTALL_PREIMAGES,a.FULL_SHA,'78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9','7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09','4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19','631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9','ad32e78548ec22d03685839858bcbccd163465125d4fe7c6b68f86dd19f65982','fbd4a68ea1d1794db939ec8a9c154b419ecfdd99924e2ca251411525649c3401')
SELF=Path(__file__)
SELF_SHA=sha(SELF.read_bytes())
LEGACY_PINS={p:sha(p.read_bytes()) for p in (ROOT/'source/adb',ROOT/'source/legacy_adb.py')}
class Guard(w.Guard):
 def check(self):
  super().check()
  require(sha(SELF.read_bytes())==SELF_SHA and sha(WIFI.read_bytes())==WIFI_SHA,'Wi-Fi SD driver changed')
  require(all(sha(p.read_bytes())==h for p,h in LEGACY_PINS.items()),'Legacy shell adapter changed')
class Journal(b.Journal):
 def __init__(self,directory,run):
  self.directory=directory
  self.state=dict(schema=1,mode='EXECUTE',run_id=run,profile='exact-linux49-microsd-probe',
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
def inputs():
 a.check_sources()
 stock,_=b.local_inputs()
 image=a.read(IMAGE)
 require(len(image)==7976960 and sha(image)==IMAGE_SHA,'Exact SD candidate required')
 full=image+bytes(b.SIZE-len(image))
 require(sha(full)==FULL_SHA,'Full padded recovery hash mismatch')
 p,s=b.unpack_image(image),b.unpack_image(stock)
 require(p['end']==len(image),'Candidate image boundary mismatch')
 require(all(p['header'][i]==s['header'][i] for i in (1,3,4,5,6,7,8,9)),'Stock header addresses/page changed')
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
 parser.add_argument('--execute',action='store_true')
 args=parser.parse_args()
 stock,candidate=inputs()
 if not args.execute:
  print(json.dumps(dict(mode='PLAN_ONLY',candidate_sha256=IMAGE_SHA,full_p10_sha256=FULL_SHA,endpoint=b.ENDPOINT,target=b.BLOCK,device_contacted=False,reboot=False)))
  return 0
 os.umask(0o077)
 for key in list(os.environ):
  if key.startswith(('ADB_','ANDROID_ADB_')) or key=='ANDROID_SERIAL':del os.environ[key]
 os.environ['PATH']=str(ROOT/'source')+os.pathsep+'/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools'+os.pathsep+os.environ.get('PATH','/usr/bin:/bin')
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
