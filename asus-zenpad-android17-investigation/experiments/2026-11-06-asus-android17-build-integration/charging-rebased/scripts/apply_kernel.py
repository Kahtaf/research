#!/usr/bin/env python3
"""Parent-owned target integration helper; default is read-only."""
from pathlib import Path
import argparse,json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];m=json.loads((R/'evidence/patch-manifest.json').read_text())
a=argparse.ArgumentParser();a.add_argument('kernel',type=Path);a.add_argument('--apply',action='store_true');args=a.parse_args();K=args.kernel.resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def run(*cmd):subprocess.run(cmd,check=True)
patch=R/'patches'/m['patch'];assert sha(patch)==m['sha256'],'changed patch'
run('git','-C',str(K),'merge-base','--is-ancestor',m['kernel_base'],'HEAD')
for path,h in m['unchanged_guards'].items():assert sha(K/path)==h,('guard requires reviewed rebase',path)
state=[sha(K/p)==v['after'] for p,v in m['files'].items()]
if all(state):print('Exact charging series already applied.');raise SystemExit(0)
for p,v in m['files'].items():assert sha(K/p)==v['before'],('overlap or missing prerequisite',p)
run('git','-C',str(K),'apply','--check','--whitespace=error-all',str(patch))
if args.apply:
 run('git','-C',str(K),'apply','--whitespace=error-all',str(patch))
 for p,v in m['files'].items():assert sha(K/p)==v['after'],p
 print('Applied exact offline series. DT permission remains absent.')
else:print('Read-only hash/guard/applicability preflight passed. No files changed.')
