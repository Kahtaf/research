#!/usr/bin/env python3
"""For the build owner: validate, optionally apply; never builds or flashes."""
from pathlib import Path
import argparse,hashlib,json,subprocess
p=argparse.ArgumentParser();p.add_argument('kernel',type=Path);p.add_argument('--apply',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[1];k=a.kernel.resolve()
manifest=json.loads((r/'evidence/patch-manifest.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
rev=subprocess.check_output(['git','-C',str(k),'rev-parse','HEAD'],text=True).strip()
if rev!='717bb3c9e13ce573cfdd2dda856debd27a0fa17f':raise SystemExit('Wrong kernel revision: '+rev+'; rebase/review required.')
if all(sha(k/f)==h['staged'] for f,h in manifest.items()):
    print('Already applied exactly. No files changed.');raise SystemExit(0)
for f,h in manifest.items():
    if sha(k/f)!=h['base']:raise SystemExit('Source differs: '+f)
for f in ['drivers/misc/mediatek/power/mt8163/asus_p00a/control.h','arch/arm64/boot/dts/mediatek/asus-p00a.dts']:
    expected=json.loads((r/'evidence/remote-source.json').read_text())['sha256'][f]
    if sha(k/f)!=expected:raise SystemExit('Charging guard input changed: '+f+'; review required.')
patch=r/'patches/0001-asus-p00a-measured-battery.patch'
subprocess.run(['git','-C',str(k),'apply','--check',str(patch)],check=True)
if a.apply:
    subprocess.run(['git','-C',str(k),'apply',str(patch)],check=True)
    for f,h in manifest.items():assert sha(k/f)==h['staged'],f
    print('Applied and all resulting source hashes verified. No build performed.')
else:print('Preflight passes. --apply applies the reviewed patch; no build is run.')
