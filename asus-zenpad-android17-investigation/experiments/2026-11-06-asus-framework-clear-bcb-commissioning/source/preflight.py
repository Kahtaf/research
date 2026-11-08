from pathlib import Path
import datetime,fcntl,hashlib,json,os,secrets,subprocess,sys
R=Path(__file__).resolve().parents[1];W=R.parent
HELPER=W/'2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
HELPER_SHA='684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
ENDPOINT='IP_REDACTED:5555'
FILES={
 'framework.oat':('/system/framework/arm64/boot-framework.oat',44179040,'d49759f44b5551e3d67516302d54a4eb1d0feb5cda6b7ea6162cae5ca0955e4a'),
 'services.odex':('/system/framework/oat/arm64/services.odex',31552208,'51f174af43fbb4bbe4c7532bf89970fb8c0eae08c17fa986150f42258e0b2e8a'),
 'uncrypt':('/system/bin/uncrypt',68752,'3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671'),
 'uncrypt.rc':('/system/etc/init/uncrypt.rc',390,'63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82'),
 'fstab':('/fstab.mt8163',2187,'9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c'),
 'policy':('/sys/fs/selinux/policy',None,'873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f'),
}
def main():
 assert hashlib.sha256(HELPER.read_bytes()).hexdigest()==HELPER_SHA
 os.umask(0o077);nonce=secrets.token_hex(8);out=R/'inputs'/nonce;out.mkdir()
 remote='/data/local/tmp/asus-framework-identity-'+nonce
 calls=[]
 def run(args,body=None,timeout=95):
  i=len(calls);(R/'evidence'/f'preflight-{nonce}-{i}-intent.json').write_text(json.dumps(dict(argv=args,body=body),indent=2)+'\n')
  p=subprocess.run(args,input=body,text=True,capture_output=True,timeout=timeout)
  calls.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
  (R/'evidence'/f'preflight-{nonce}-calls.json').write_text(json.dumps(calls,indent=2)+'\n')
  if p.returncode:raise RuntimeError('Preflight failed; no API invocation; preserve staging')
  return p.stdout
 with (W/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  descriptor=run(['adb','-s',ENDPOINT,'shell','service','list'])
  recovery=[line.strip() for line in descriptor.splitlines() if 'recovery:' in line]
  assert len(recovery)==1 and recovery[0].split('\t')[-1]=='recovery: [android.os.IRecoverySystem]',recovery
  body=f'''set -eu
[ "$(getprop ro.hardware)" = mt8163 ]
[ "$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para)" = /dev/block/mmcblk0p12 ]
if pidof uncrypt; then exit 91; fi
[ ! -e /dev/socket/uncrypt ]
[ "$(getprop init.svc.uncrypt)" != running ]
[ "$(getprop init.svc.setup-bcb)" != running ]
[ "$(getprop init.svc.clear-bcb)" != running ]
ls -Zd /dev/block/mmcblk0p12
ls -l /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para
[ ! -e {remote} ]
[ ! -L {remote} ]
mkdir {remote}
chmod 700 {remote}
'''
  for name,(path,size,pin) in FILES.items():
   body+=f'cp {path} {remote}/{name}\nchown 2000:2000 {remote}/{name}\nchmod 600 {remote}/{name}\n'
  body+=f'chmod 711 {remote}\n'
  identity=run([sys.executable,str(HELPER)],body)
  pins={}
  for name,(path,size,pin) in FILES.items():
   run(['adb','-s',ENDPOINT,'pull',remote+'/'+name,str(out/name)],timeout=60)
   p=out/name;actual=hashlib.sha256(p.read_bytes()).hexdigest()
   assert not p.is_symlink() and actual==pin,(name,actual)
   if size is not None:assert p.stat().st_size==size
   pins[path]=dict(bytes=p.stat().st_size,sha256=actual)
  cleanup=f'''set -eu
[ ! -L {remote} ]
[ "$(stat -c '%u:%g:%a' {remote})" = 0:0:711 ]
'''
  for name in FILES:
   cleanup+=f'''[ ! -L {remote}/{name} ]
[ "$(stat -c '%u:%g:%a:%h' {remote}/{name})" = 2000:2000:600:1 ]
'''
  cleanup+='rm '+' '.join(remote+'/'+n for n in FILES)+f'\nrmdir {remote}\n'
  run([sys.executable,str(HELPER)],cleanup)
 result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),nonce=nonce,descriptor=recovery[0],files=pins,live_metadata=identity,staging_cleaned=True,api_invoked=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (R/'evidence/live-preflight.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
