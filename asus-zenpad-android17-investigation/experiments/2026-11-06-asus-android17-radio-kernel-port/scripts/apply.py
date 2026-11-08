#!/usr/bin/env python3
"""Default is preflight. Apply only these patches; never overwrite an overlay tree."""
import argparse,hashlib,json,pathlib,subprocess
r=pathlib.Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('kernel',type=pathlib.Path);a.add_argument('--apply',action='store_true');args=a.parse_args();root=args.kernel.resolve()
manifest=json.loads((r/'evidence/kernel-patch-manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
if all(sha(root/k)==v['after_sha256'] for k,v in manifest.items()):
 print('Exact radio patches already applied.');raise SystemExit(0)
for path,entry in manifest.items():
 actual=sha(root/path)
 if actual!=entry['before_sha256']:raise SystemExit(f'Overlapping or partial change: {path}; expected pristine radio preimage. Do not force it.')
patches=[str(r/'patches'/name) for name in ['0001-import-asus-mt8163-radio.patch','0002-wire-mt8163-radio-kbuild.patch']]
subprocess.run(['git','-C',str(root),'apply','--check','--whitespace=nowarn',*patches],check=True)
if args.apply:
 subprocess.run(['git','-C',str(root),'apply','--whitespace=nowarn',*patches],check=True)
 assert all(sha(root/k)==v['after_sha256'] for k,v in manifest.items())
 print('Applied exact radio import and Kbuild patches.')
else:print('Radio preimages and both patches verified; pass --apply to apply.')
