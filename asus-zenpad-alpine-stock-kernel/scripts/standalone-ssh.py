#!/usr/bin/env python3
"""Pinned SSH commands on the currently verified independent Alpine boot."""
from pathlib import Path
import argparse,json,subprocess
HERE=Path(__file__).resolve().parents[1]
def args():
 d=json.loads((HERE/'private/standalone-ssh.json').read_text())
 return ['ssh','-i',str(HERE/'private/alpine-trial-key'),'-p',str(d['port']),'-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(HERE/'private/standalone-known-hosts'),'-o','ConnectTimeout=8','root@'+d['host']],d

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('script',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--timeout',type=int,default=50);a=p.parse_args()
 assert 1<=a.timeout<=600
 cmd,d=args();guard='[ "$(cat /proc/sys/kernel/random/boot_id)" = "'+d['expected_boot_id']+'" ] && [ "$(uname -r)" = 3.18.35 ] && [ "$(cat /etc/asus-alpine-ram-release)" = asus-alpine-stock-kernel-v1 ] || exit 91\n'
 try:
  r=subprocess.run(cmd+['timeout','-k','2',str(a.timeout),'/bin/sh','-s'],input=guard+a.script.read_text(),text=True,capture_output=True,timeout=a.timeout+12)
 except subprocess.TimeoutExpired as error:
  def decoded(value):return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
  a.output.write_text(decoded(error.stdout));a.output.with_suffix(a.output.suffix+'.stderr').write_text(decoded(error.stderr)+'\nHOST_OBSERVATION_TIMEOUT; remote completion unknown\n')
  print('PINNED_STANDALONE_SSH_OBSERVATION_TIMEOUT OUTPUT',a.output)
  raise SystemExit(124)
 a.output.write_text(r.stdout);a.output.with_suffix(a.output.suffix+'.stderr').write_text(r.stderr)
 print('PINNED_STANDALONE_SSH_EXIT',r.returncode,'OUTPUT',a.output)
 raise SystemExit(r.returncode)
if __name__=='__main__':main()
