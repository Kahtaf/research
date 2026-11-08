#!/usr/bin/env python3
"""Generate deterministic patches against the exact committed connectivity subtree."""
from pathlib import Path
import difflib,hashlib,json
r=Path(__file__).resolve().parents[1];base=r/'sourceinputs/kernel-base-717bb3c9';new=r/'stagedpatches/kernel-input';out=r/'patches';out.mkdir(exist_ok=True)
added=[];edited=[];manifest={}
for p in sorted(new.rglob('*')):
 if not p.is_file() or p.name.startswith('._'):continue
 rel=p.relative_to(new);old=base/rel;data=p.read_bytes();before=old.read_bytes() if old.exists() else None
 if before==data:continue
 # All imported source files are text. No calibration or prebuilt kernel object.
 text=data.decode();prior=before.decode() if before is not None else ''
 header=f'diff --git a/{rel} b/{rel}\n'
 if before is None:header+='new file mode 100644\n'
 lines=list(difflib.unified_diff(prior.splitlines(True),text.splitlines(True),fromfile=f'a/{rel}' if before is not None else '/dev/null',tofile=f'b/{rel}'))
 diff=''.join(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n' for line in lines)
 if not diff:continue
 (added if before is None else edited).append(header+diff)
 manifest[str(rel)]={'before_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,'after_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
(out/'0001-import-asus-mt8163-radio.patch').write_text(''.join(added))
(out/'0002-wire-mt8163-radio-kbuild.patch').write_text(''.join(edited))
(r/'evidence/kernel-patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Imported',len(added),'files; changed',len(edited),'existing files')
