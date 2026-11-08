#!/usr/bin/env python3
"""Offline rebuild into a NEW directory; no target or remote commands."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
LLD='/OWNER_HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/rust-lld'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 log=[]
 def run(cmd):
  p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True);log.append(dict(argv=[str(x) for x in cmd],rc=p.returncode,stdout=p.stdout,stderr=p.stderr))
  (a.out/'commands.json').write_text(json.dumps(log,indent=2)+'\n')
  if p.returncode:raise RuntimeError(p.stderr)
 src=ROOT/'source';stock=ROOT.parent/'2026-11-05-asus-boot-access-audit/artifacts/device-backup'
 run([sys.executable,'-B',src/'build_tools.py','--out',a.out/'tools','--lld',LLD])
 run([sys.executable,'-B',src/'generate.py','--recovery',stock/'initial/recovery.bin','--recovery-verify',stock/'verify/recovery.bin','--public-key',ROOT/'artifacts/inputs/adbkey.pub','--tools',a.out/'tools','--out',a.out/'candidate'])
 run([sys.executable,'-B',src/'verify.py','--candidate',a.out/'candidate','--tools',a.out/'tools','--stock',stock/'initial/recovery.bin','--out',a.out/'verification.json'])
 run([sys.executable,'-B',src/'build_rescue.py','--out',a.out/'rescue','--lld',LLD])
 matches={}
 for left,right in [(a.out/'tools/diag',ROOT/'artifacts/tools-final/diag'),(a.out/'candidate/UNTESTED-stock-control.img',ROOT/'artifacts/candidate-final/UNTESTED-stock-control.img'),(a.out/'candidate/diagnostic-sepolicy',ROOT/'artifacts/candidate-final/diagnostic-sepolicy'),(a.out/'rescue/rescue-UNARMED',ROOT/'artifacts/rescue-v1/rescue-UNARMED')]:
  b=left.read_bytes();assert b==right.read_bytes();matches[str(right.relative_to(ROOT))]=hashlib.sha256(b).hexdigest()
 (a.out/'reproduction.json').write_text(json.dumps(dict(byte_identical=matches,target_executed=False),indent=2)+'\n')
 print(json.dumps(matches,indent=2))
if __name__=='__main__':main()
