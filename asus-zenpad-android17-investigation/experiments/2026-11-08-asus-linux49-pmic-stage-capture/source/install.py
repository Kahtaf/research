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
IMAGE_SHA='df9ad602f617fc3e3191ac298b496e7d3d028509b4d6892329f2c0212260a26b'
FULL_SHA='bcf85635198721759d6f4f24f2e7311ca9bf594d7dae698cec8c169a8219f735'
INSTALL_PREIMAGES=(*a.INSTALL_PREIMAGES,a.FULL_SHA,'78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9','7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09','4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19','631cebb6df7be4b08edb713c976799ac60b4552e2caa3d4f1ea15b11a37610b9','5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453','a0e4856da4138dd401461add3104005fca67cf495da1a605c02392244dd757f8','c9d4506c90fa12f6a77a5e34368312307903eb9e0c04d47d5461f2e455b062e3','4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26','e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0','c1fe664108ee8e2ef24edc9f0b3249589dc227f0ee8502b63e224930ee7fa541','81bc90ed8f8c25a291c8ffca205de94a0188b5cbab37379b3f667ad1ac42ba2d','039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba','a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d','80270c24e310b5dd2a8e1e9e21b35a2f3d39c87dc2db25271d97b7d85da733eb','ed054366765198d628f62086627a753daeae645cadf1d431be0e11315a649bbe','c89bedfba2bd8550580f394bb4774018523855b622851d563a56975746f99bb5','8e002fd9f9b7797470fd03d94da44c0f3479c6fdfefe00b8ecd1136bc53534fb','14a651dc2c1862f2d8a68153134d95864db495d0382f687a617ff27513e9c1c6','764aaab335c1e2192c4bc97d123ee044dada09c4798fbbfcb7b7102d66b8bd33','aded4e0d2b6418d69f824d0b0b1d1ebbf2e646aafe60da988111c3a04e349e3c','928efe92e7c8e617c571cd7512037be374d6c18815cb5303c37ae5e30465178d','88f79cc02d71bfe0708d6be77d66d06d3107befcee3d5d0225ecc8134942f617','39241265432908288561ce54d8dde8ae28f55ce97468b3193251444f6a43c52c','e4afdc3542ecfbc5a4105ab6eb9d5b9f78ff614c2455b8e0b8dee5932e7ad3f4','4b474d6e714871dcefbba9510ff3d25f66e13147171ae39b0fa670c7cd70402e','5f07084ea1c5df8c6d6e76f99be264149c19b77a0a9265cc6a05db3b6258a412','ab1b388b1f48365edb5d0b554ac4151debe32638758aea0bd1ef1ea4b20b6ea6','49e6519e4c4447b8c0b334e9991e8b011a6943cbcf79550648a33a5074bcfd4b','7418c5d3a43c0b458311d880ec87f0d6b781794998d688153f31c3383f7c3752','e4df271f2024c2abcfeac80475a074541255ae8318d86f77771a9e5684d93b0f')
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
  self.state=dict(schema=1,mode='EXECUTE',run_id=run,profile='exact-linux49-pmic-stage-a1ff82b1-r1',
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
 require(len(image)==7987200 and sha(image)==IMAGE_SHA,'Exact SD candidate required')
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
