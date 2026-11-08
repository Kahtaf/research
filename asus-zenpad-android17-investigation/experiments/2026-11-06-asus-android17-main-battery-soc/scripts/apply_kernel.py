#!/usr/bin/env python3
"""Exact, incremental application. Default is read-only validation."""
from pathlib import Path
import argparse,json,hashlib,subprocess
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('kernel',type=Path);a.add_argument('--apply',action='store_true');args=a.parse_args()
m=json.loads((R/'evidence/patch-manifest.json').read_text());kernel=args.kernel.resolve()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
wrong_guards=[p for p,h in m['guard_files'].items() if digest(kernel/p)!=h]
if wrong_guards:raise SystemExit('Charging guard or measurement route differs; review required:\n'+'\n'.join(wrong_guards))
files=m['kernel_files'];states={p:digest(kernel/p) for p in files}
if all(states[p]==v['after'] for p,v in files.items()):
 print('Exact SOC patch already present; no writes.');raise SystemExit(0)
wrong=[p for p,v in files.items() if states[p]!=v['before']]
if wrong:raise SystemExit('Wrong predecessor (apply the measurement patch first, or review overlapping changes):\n'+'\n'.join(wrong))
patch=R/'patches/0002-asus-p00a-checked-main-battery-soc.patch'
if digest(patch)!=m['patches'][patch.name]['sha256']:raise SystemExit('Patch hash mismatch')
# No whitespace relaxation or three-way merge; unexpected changes require review.
subprocess.run(['git','-C',str(kernel),'apply','--check','--whitespace=error-all',str(patch)],check=True)
if args.apply:
 subprocess.run(['git','-C',str(kernel),'apply','--whitespace=error-all',str(patch)],check=True)
 if any(digest(kernel/p)!=v['after'] for p,v in files.items()):raise SystemExit('Post-apply hash mismatch')
 print('Applied exact incremental SOC patch. No configuration/build performed.')
else:print('Exact post-measurement inputs and git apply --check pass; no writes.')
