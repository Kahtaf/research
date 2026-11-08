from pathlib import Path
import json
from dex import Dex
S=Path(__file__).resolve().parents[1]
targets=['Landroid/os/IRecoverySystem;', 'Landroid/os/IRecoverySystem$Stub;', 'Landroid/os/IRecoverySystem$Stub$Proxy;', 'Lcom/android/server/RecoverySystemService;', 'Lcom/android/server/RecoverySystemService$Lifecycle;', 'Landroid/app/ContextImpl;', 'Landroid/app/ActivityManager;', 'Lcom/android/server/am/ActivityManagerService;']
out=[]
for path in sorted((S/'inputs').glob('*.dex*')):
 d=Dex(path)
 for name in targets:
  if name not in d.classes:continue
  c=d.classdata(name);c['file']=str(path.relative_to(S));out.append(c)
  print(c['file'],name)
  for m in c['methods']:
   if 'Recovery' in name or any(x in m['name'] for x in ('checkPermission(','checkComponentPermission(','enforceCallingOrSelfPermission(','checkCallingOrSelfPermission(')):
    print(' ',hex(m['code_offset']),m['name'])
(S/'evidence/class-index.json').write_text(json.dumps(out,indent=2)+'\n')
