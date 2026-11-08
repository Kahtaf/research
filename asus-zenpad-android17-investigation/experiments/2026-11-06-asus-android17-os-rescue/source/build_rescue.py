#!/usr/bin/env python3
"""Only local compilers and offline fake boundary tests. No target execution."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--lld',required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 log=[]
 commands=[['clang','-O2','-Wall','-Wextra','-Werror','-dynamiclib',str(ROOT/'source/rescue_gate.c'),'-o',str(a.out/'librescue_gate.dylib')],
 ['clang','--target=aarch64-linux-gnu','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pic','-fno-pie','-Wall','-Wextra','-Werror','-DRESCUE_UNARMED','-c',str(ROOT/'source/rescue_gate.c'),'-o',str(a.out/'rescue_gate.o')],
 [a.lld,'-flavor','gnu','-m','aarch64elf','-static','--build-id=none','-e','_start','-o',str(a.out/'rescue-UNARMED'),str(a.out/'rescue_gate.o')]]
 for cmd in commands:
  p=subprocess.run(cmd,capture_output=True,text=True);log.append(dict(argv=cmd,rc=p.returncode,stdout=p.stdout,stderr=p.stderr))
  if p.returncode:break
 (a.out/'build.json').write_text(json.dumps(log,indent=2)+'\n')
 if p.returncode:raise SystemExit(p.returncode)
 print('Compiled host fixed gate and ARM64 UNARMED refusal-only helper. No runtime adapter.')
if __name__=='__main__':main()
