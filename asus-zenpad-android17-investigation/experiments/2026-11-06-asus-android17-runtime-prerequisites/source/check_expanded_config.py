from pathlib import Path
import json,sys
R=Path('/srv/android/asus-android17-runtime-prereqs')
def cfg(path):
 d={}
 for l in path.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
p=cfg(R/'inputs/physical.config');g=cfg(Path(sys.argv[1]))
keys=sorted(k for k in p if k.startswith(('CONFIG_EROFS','CONFIG_EXT4','CONFIG_DM_','CONFIG_BLK_DEV_DM','CONFIG_BLK_DEV_LOOP','CONFIG_ANDROID_BINDER','CONFIG_SECURITY_SELINUX','CONFIG_LZ4')) or k in ['CONFIG_MISC_FILESYSTEMS','CONFIG_AUDIT','CONFIG_SECURITY','CONFIG_SECURITY_NETWORK','CONFIG_DEFAULT_SECURITY'])
c={k:{'physical':p[k],'guest':g.get(k,'n'),'equal':p[k]==g.get(k,'n')} for k in keys}
(R/'evidence'/('config-expanded-comparison-'+Path(sys.argv[1]).parent.name.removeprefix('build-')+'.json')).write_text(json.dumps(c,indent=2)+'\n')
print('differences',[(k,v) for k,v in c.items() if not v['equal']]);assert all(v['equal'] for v in c.values())
