#!/usr/bin/env python3
"""Observe a new SD boot through the saved host key, then update the boot guard."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,time,uuid
HERE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('link',HERE/'scripts/standalone-ssh.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cmd,old=m.args();cmd=['ConnectTimeout=2' if x=='ConnectTimeout=8' else x for x in cmd]
script='''set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
assert os.uname().release=='3.18.35' and os.uname().machine=='aarch64'
assert Path('/etc/asus-alpine-ram-release').read_text().strip()=='asus-alpine-stock-kernel-v1'
assert Path('/proc/1/comm').read_text().strip()=='init'
assert Path('/run/asus-alpine/root-mode').read_text().strip()=='SD-loop'
p=Path('/dev/mmcblk0p12');s=p.stat();assert stat.S_ISBLK(s.st_mode) and s.st_rdev==os.makedev(179,12)
assert Path('/sys/class/block/mmcblk0p12/start').read_text().strip()=='225576'
with p.open('rb') as f:bcb=f.read(2048)
assert bcb==b'boot-recovery'+bytes(2048-len(b'boot-recovery'))
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'mode':'SD-loop','kernel':'3.18.35','persistent_bcb_command':'boot-recovery','recovery_arguments':'empty','bcb_sha256':hashlib.sha256(bcb).hexdigest()}))
PY
'''
deadline=time.monotonic()+110;last=''
while time.monotonic()<deadline:
 r=subprocess.run(cmd+['sh','-s'],input=script,text=True,capture_output=True,timeout=12)
 if r.returncode==0:
  state=json.loads(r.stdout);uuid.UUID(state['boot_id'])
  if state['boot_id']==old['expected_boot_id']:
   time.sleep(2)
   continue
  a.output.write_text(json.dumps(state,indent=2)+'\n')
  old['expected_boot_id']=state['boot_id'];(HERE/'private/standalone-ssh.json').write_text(json.dumps(old)+'\n')
  print('NEW_SD_BOOT_VERIFIED_USING_PREVIOUSLY_PINNED_HOST_KEY; BCB persists with empty arguments');break
 if r.returncode!=255:
  a.output.with_suffix('.stderr').write_text(r.stderr)
  raise SystemExit('Authenticated host failed boot assertions; inspect saved error')
 last=r.stderr;time.sleep(2)
else:
 a.output.with_suffix('.stderr').write_text(last)
 raise SystemExit('No authenticated SD boot within observer deadline; inspect USB next')
