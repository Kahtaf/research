#!/usr/bin/env python3
"""One ready-signalled SSH workload, bounded root window and private output."""
from pathlib import Path
import json, secrets, subprocess, time
HERE=Path(__file__).resolve().parents[1]
access=json.loads((HERE/'private/ACCESS.json').read_text())
adb=['adb','-s',access['usb_serial']]
marker='/data/local/tmp/asus-alpine-ready-'+secrets.token_hex(8)
root_script=f'''R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
chroot "$R" /usr/bin/timeout 30 /usr/sbin/sshd -D -e -p 2223 -o PidFile=/run/sshd-bounded.pid </dev/null >"$R/tmp/sshd-bounded.log" 2>&1 &
p=$!
trap 'kill "$p" 2>/dev/null || true; rm -f {marker}' EXIT
sleep 1
getenforce > {marker}
chmod 644 {marker}
sleep 18
'''
log=HERE/'private/live/experiment-03e-root-window.txt'
err=HERE/'private/live/experiment-03e-root-window.stderr'
with log.open('w') as out, err.open('w') as errors:
 proc=subprocess.Popen(['python3',str(HERE.parent/'2026-11-07-asus-usb-retained-log-collector/scripts/root_shell_usb.py')],stdin=subprocess.PIPE,stdout=out,stderr=errors,text=True)
 proc.stdin.write(root_script);proc.stdin.close()
 ready=False
 for _ in range(24):
  if proc.poll() is not None: break
  status=subprocess.run(adb+['shell','cat',marker],capture_output=True,text=True,timeout=3)
  if status.returncode==0:
   assert status.stdout.strip()=='Permissive',status.stdout
   ready=True;break
  time.sleep(.25)
 if ready:
  host='127.0.0.1'
  forwarded=subprocess.check_output(adb+['forward','tcp:0','tcp:2223'],text=True,timeout=4).strip()
  assert forwarded.isdecimal()
  command='cat /etc/alpine-release; uname -rm; id; python3 -c \'import sqlite3; c=sqlite3.connect("/tmp/workload.sqlite"); c.execute("create table if not exists readings(value integer)"); c.execute("insert into readings values (42)"); c.commit(); print(c.execute("select count(*),sum(value) from readings").fetchone())\'; curl -fsS --max-time 8 https://alpinelinux.org/ -o /tmp/ssh-workload.html; wc -c /tmp/ssh-workload.html'
  result=subprocess.run(['ssh','-i',str(HERE/'private/alpine-trial-key'),'-p',forwarded,'-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=accept-new','-o','UserKnownHostsFile='+str(HERE/'private/alpine-trial-known-hosts'),'-o','ConnectTimeout=5','root@'+host,command],capture_output=True,text=True,timeout=12)
  (HERE/'private/live/experiment-03e-ssh-workload.txt').write_text(result.stdout)
  (HERE/'private/live/experiment-03e-ssh-workload.stderr').write_text(result.stderr)
  print('SSH_WORKLOAD_EXIT',result.returncode)
  subprocess.run(adb+['forward','--remove','tcp:'+forwarded],check=True,timeout=4)
 else: print('NO_VERIFIED_READY_WINDOW')
 print('ROOT_WRAPPER_EXIT',proc.wait(timeout=35))
