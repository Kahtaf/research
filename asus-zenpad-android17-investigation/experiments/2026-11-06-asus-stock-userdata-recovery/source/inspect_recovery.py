from pathlib import Path
import json,re
from elfaudit import ELF
S=Path(__file__).resolve().parents[1]
e=ELF(S/'inputs/recovery__sbin_recovery')
terms=['/data','/cache','/persist','/nvram','/metadata','/protect_f','/protect_s','/proinfo','Wiping data','Data wipe','wipe data/factory reset','Yes -- delete all user data','/misc','/dev/block','No command','sideload','reboot system now','Wipe data','--wipe_data','boot-recovery','/cache/recovery','/cache/recovery/command']
refs=e.stringrefs(terms)
(S/'evidence/recovery-stringrefs.json').write_text(json.dumps(refs,indent=2)+'\n')
windows=[]
for x in refs:
 a=int(x['pc'],16);windows.append(x['string']+'\n'+e.listing(max(0x4001c0,a-48),a+96))
(S/'evidence/recovery-reference-windows.txt').write_text('\n'.join(windows))
for name,a,b in [('format',0x407cc0,0x408450),('wipe-block',0x41b1d0,0x41b370),('file-size',0x416618,0x416780)]:
 (S/f'evidence/{name}.txt').write_text(e.listing(a,b))
print(json.dumps(refs,indent=2))
