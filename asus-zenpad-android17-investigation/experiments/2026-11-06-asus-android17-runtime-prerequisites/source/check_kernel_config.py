from pathlib import Path
import json,re,sys
R=Path('/srv/android/asus-android17-runtime-prereqs')
def config(p):
 d={}
 for line in p.read_text().splitlines():
  if line.startswith('CONFIG_'): k,v=line.split('=',1);d[k]=v
  elif line.startswith('# CONFIG_') and line.endswith(' is not set'):d[line.split()[1]]='n'
 return d
p=config(R/'inputs/physical.config');g=config(Path(sys.argv[1]));prefixes=('CONFIG_EROFS','CONFIG_ANDROID_BINDER','CONFIG_BLK_DEV_LOOP','CONFIG_DM_VERITY','CONFIG_SECURITY_SELINUX','CONFIG_EXT4_FS','CONFIG_CRYPTO_SHA256')
keys=sorted(k for k in p if k.startswith(prefixes));report={k:{'physical':p[k],'guest':g.get(k,'n'),'equal':p[k]==g.get(k,'n')} for k in keys}
(R/'evidence/config-comparison-r2.json').write_text(json.dumps(report,indent=2)+'\n')
for k,v in report.items():
 if not v['equal']:print(k,v)
assert all(v['equal'] for v in report.values()),'Correct fixture config before kernel compilation'
