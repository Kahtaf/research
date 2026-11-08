from pathlib import Path
import remote,json,base64
R=Path(__file__).resolve().parents[1]
files={n:base64.b64encode((R/'evidence'/n).read_bytes()).decode() for n in ['obsolete-reader-terminal.log','obsolete-reader-local-terminal.json']}
s='FILES='+repr(files)+'\n'+r'''
from pathlib import Path
import json,hashlib,base64,datetime
R=Path('/srv/android/asus-reviewed-build-kit/r9');M=Path('/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1');P=Path('/srv/android/asus-product-integration-staging/r9/webview.apk')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for name,b in FILES.items():
 with (R/'evidence'/name).open('xb') as f:f.write(base64.b64decode(b))
cleanup=json.loads((R/'evidence/obsolete-reader-cleanup.json').read_text());local=json.loads((R/'evidence/obsolete-reader-local-terminal.json').read_text())
assert cleanup['outcome']=='TERMINATED_AFTER_TERM' and cleanup['signals']==[dict(pid=1679682,signal='TERM',identity=cleanup['candidates'][0])]
assert local['remaining_exact_handles']==''
assert sha(M/'pins.json')=='3e6ca30a3074cdd7f19dd522111c52fadbfdb311a3aa16fd23563c9011e35437'
for rel,digest in json.loads((M/'pins.json').read_text()).items():assert sha(M/rel)==digest and (M/rel).stat().st_mode&0o222==0
assert P.stat().st_size==260835655 and sha(P)=='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a'
assert json.loads((R/'evidence/selected-lfs-audit.json').read_text())['status']=='REJECTED_AUDIT_NOT_ADMITTED'
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),outcome='OWNED_READER_TERMINATED_AFTER_SINGLE_TERM',remote_pid=1679682,remote_uid=1001,start_ticks=3292870,ssh_client_port=50161,local_wrapper_pid=9069,local_ssh_pid=9071,local_handles_absent=True,kill_used=False,parent_sshd_native_other_worker_signals=False,payload_and_frozen_milestone_pins_unchanged=True,rejection_sentinel_preserved=True,proof_path=str(R/'evidence/obsolete-reader-cleanup.json'),proof_sha256=sha(R/'evidence/obsolete-reader-cleanup.json'),obsolete_terminal_log_sha256=sha(R/'evidence/obsolete-reader-terminal.log'),uncertainty=None)
with (R/'evidence/cleanup-summary.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);(R/'evidence/cleanup-summary.json').write_text(r);print(r)
