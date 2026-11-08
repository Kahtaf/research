#!/usr/bin/env python3
"""Read-only source capture on the already authorized builder; no remote writes."""
import hashlib, json, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
SSH=['ssh','-i',str(pathlib.Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
REMOTE=r'''
from pathlib import Path
import hashlib,json,os
K=Path('/srv/android/asus-build-continuation/kernel');A=Path('/srv/android/lineage24')
files={}
for group,root,names in [('kernel',K,['init/main.c','arch/arm64/kernel/setup.c','arch/arm64/mm/init.c','drivers/of/fdt.c','security/selinux/hooks.c','security/selinux/Kconfig']),('aosp',A,['system/core/init/selinux.cpp','system/core/init/Android.bp','system/core/init/property_service.cpp','system/core/init/init.cpp','system/core/init/first_stage_init.cpp','system/core/init/first_stage_mount.cpp','system/core/init/block_dev_initializer.cpp','system/fs/fs_mgr/libfstab/boot_config.cpp','system/fs/fs_mgr/libfstab/fstab.cpp','device/asus/p00a/BoardConfig.mk','device/asus/p00a/rootdir/fstab.mt8163','build/release/flag_values/trunk_staging/RELEASE_PLATFORM_SDK_VERSION.textproto','build/release/flag_values/cp2a/RELEASE_PLATFORM_SDK_VERSION.textproto'])]:
 for n in names:
  p=root/n
  if p.is_file():
   b=p.read_bytes();files[group+'/'+n]={'remote_path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode()}
  else:files[group+'/'+n]={'missing':True,'remote_path':str(p)}
matches=[];count=0;digest=hashlib.sha256()
for d,dirs,names in os.walk(K,followlinks=False):
 dirs[:]=sorted(x for x in dirs if x not in ('.git',))
 for name in sorted(names):
  p=Path(d)/name
  if p.suffix not in ('.c','.h','.S') or p.is_symlink():continue
  b=p.read_bytes();count+=1;rel=str(p.relative_to(K));h=hashlib.sha256(b).hexdigest();digest.update((rel+' '+h+'\n').encode())
  if b'bootopt' in b or b'build_version' in b:
   lines=[{'line':i,'text':t} for i,t in enumerate(b.decode(errors='replace').splitlines(),1) if 'bootopt' in t or 'build_version' in t]
   matches.append({'path':rel,'sha256':h,'lines':lines})
print(json.dumps({'files':files,'kernel_argument_search':{'file_count':count,'sorted_walk_manifest_sha256':digest.hexdigest(),'suffixes':['.c','.h','.S'],'symlinks_followed':False,'matches':matches}}))
'''
r=subprocess.run(SSH+['python3 -'],input=REMOTE,text=True,capture_output=True,check=True)
data=json.loads(r.stdout)
for name,record in data['files'].items():
 if 'text' not in record:continue
 text=record.pop('text');p=ROOT/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
(ROOT/'evidence/source-receipts.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
