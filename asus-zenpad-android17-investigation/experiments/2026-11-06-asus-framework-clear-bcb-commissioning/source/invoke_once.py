"""One exact OEM Binder request, no raw writer/reboot/retry or daemon launcher."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[1];W=R.parent
HELPER=W/'2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
HELPER_SHA='684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
READ=W/'2026-11-06-asus-pending-recovery-request'
BEFORE='8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9'
AFTER='8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef'
BODY='''set -eu
[ "$(getprop ro.hardware)" = mt8163 ]
[ "$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para)" = /dev/block/mmcblk0p12 ]
[ "$(cat /sys/class/block/mmcblk0p12/partition)" = 12 ]
[ "$(cat /sys/class/block/mmcblk0p12/start)" = 225576 ]
[ "$(cat /sys/class/block/mmcblk0p12/size)" = 1024 ]
[ "$(cat /sys/class/block/mmcblk0p12/dev)" = 179:12 ]
[ "$(cat /sys/class/block/mmcblk0/queue/logical_block_size)" = 512 ]
if pidof uncrypt; then exit 91; fi
[ ! -e /dev/socket/uncrypt ]
for asus_property in init.svc.uncrypt init.svc.setup-bcb init.svc.clear-bcb; do
asus_state=$(getprop "$asus_property")
case "$asus_state" in ''|stopped) ;; *) exit 91 ;; esac
done
printf 'ASUS_FRAMEWORK_BCB_BEGIN\\n'
/system/bin/service call recovery 3
printf 'ASUS_FRAMEWORK_BCB_END\\n'
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc)
def dump(path,record,exclusive=False):
 flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_EXCL if exclusive else os.O_TRUNC)
 fd=os.open(path,flags,0o600)
 try:
  with os.fdopen(fd,'w',closefd=False) as f:
   json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(fd)
 finally:os.close(fd)
 dfd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(dfd)
 finally:os.close(dfd)
def parse_reply(stdout):
 if stdout.count('ASUS_FRAMEWORK_BCB_BEGIN\n')!=1 or stdout.count('ASUS_FRAMEWORK_BCB_END\n')!=1:
  return None
 inner=stdout.split('ASUS_FRAMEWORK_BCB_BEGIN\n')[1].split('ASUS_FRAMEWORK_BCB_END\n')[0]
 match=re.fullmatch(r"Result: Parcel\(00000000 0000000([01])\s+'\.{8}'\)\r?\n",inner)
 return bool(int(match[1])) if match else None
def validate_review(review,expected):
 path=R/'evidence/parent-review.json'
 assert sha(path)==expected
 assert review['approved'] is True
 assert review['transaction']==3 and review['arguments']==[] and review['retry'] is False
 assert review['source_sha256']==sha(Path(__file__)) and sha(HELPER)==HELPER_SHA
 assert now()<datetime.datetime.fromisoformat(review['expires_utc'])-datetime.timedelta(seconds=90)
 for name,pin in review['evidence_pins'].items():assert sha(W/name)==pin
 capture_path=W/review['before_receipt']
 capture=json.loads(capture_path.read_text());assert capture['both_match_expected'] and capture['staging_cleanup_verified']
 age=(now()-datetime.datetime.fromisoformat(capture['at_utc'])).total_seconds()
 assert 0<=age<180
 assert len(capture['files'])==2
 for item in capture['files']:
  path=READ/item['path'];assert not path.is_symlink()
  b=path.read_bytes();assert len(b)==524288 and hashlib.sha256(b).hexdigest()==BEFORE
  assert hashlib.sha256(bytes(1088)+b[1088:]).hexdigest()==AFTER
 return capture
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--review-sha256');args=p.parse_args()
 if not args.execute:
  print(json.dumps(dict(mode='PLAN_ONLY',call='/system/bin/service call recovery 3',arguments=[],retry=False,reboot=False,device_contacted=False)));return
 os.umask(0o077)
 review=json.loads((R/'evidence/parent-review.json').read_text())
 with (W/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  validate_review(review,args.review_sha256)
  record=dict(utc=now().isoformat(),outcome='UNKNOWN',possibly_submitted=True,review_sha256=args.review_sha256,body_sha256=hashlib.sha256(BODY.encode()).hexdigest(),retry=False,reboot=False)
  # Irrevocably consumes this API attempt before starting the helper. Never
  # replay on timeout, refusal, partial journal publication or controller restart.
  dump(R/'evidence/api-attempt.json',record,exclusive=True)
  start=time.monotonic()
  try:
   result=subprocess.run([sys.executable,str(HELPER)],input=BODY,text=True,capture_output=True,timeout=95)
   reply=parse_reply(result.stdout) if result.returncode==0 else None
   record.update(elapsed_seconds=time.monotonic()-start,helper_exit=result.returncode,stdout=result.stdout,stderr=result.stderr,framework_reply=reply,call_return_observed=(result.returncode==0 and 'ASUS_FRAMEWORK_BCB_END\n' in result.stdout),outcome='API_TRUE_NEEDS_READBACK' if reply is True else 'API_FALSE_NEEDS_READBACK' if reply is False else 'UNKNOWN')
  except (OSError,UnicodeError,subprocess.TimeoutExpired) as exc:
   record.update(elapsed_seconds=time.monotonic()-start,error=repr(exc))
  dump(R/'evidence/api-result.json',record,exclusive=True)
  print(json.dumps(record,indent=2))
if __name__=='__main__':main()
