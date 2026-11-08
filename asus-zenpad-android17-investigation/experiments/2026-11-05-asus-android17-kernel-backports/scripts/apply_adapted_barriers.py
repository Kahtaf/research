#!/usr/bin/env python3
"""Resolve only the documented first EROFS prerequisite conflict, then resume."""
import hashlib,json,subprocess
from pathlib import Path
root=Path('/srv/android/asus-android17');source=root/'kernel'
patch=root/'patches/0001-mt8163-conditional-barriers.patch'
subprocess.run(['git','am','--abort'],cwd=source,check=True)
subprocess.run(['git','am',str(patch)],cwd=source,check=True)
p=root/'logs/erofs-import.json';ledger=json.loads(p.read_text())
ledger.append(dict(source_commit='0977ab3a1693867dd1577aa2a237addc872ac523',
    patch=str(patch.relative_to(root)),sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
    result='applied',adaptation='Supply missing acquire wrappers over existing 4.9 primitives; preserve ordering',
    local_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()))
p.write_text(json.dumps(ledger,indent=2)+'\n')
subprocess.run(['python3','/srv/android/prepare_erofs.py'],check=True)
