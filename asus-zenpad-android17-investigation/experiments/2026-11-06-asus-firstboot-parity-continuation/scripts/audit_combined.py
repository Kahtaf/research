from pathlib import Path
import json,hashlib,datetime
R=Path('/srv/android/asus-firstboot-parity-continuation');P=Path('/srv/android/asus-firstboot-runtime'); C=Path('/srv/android/asus-build-continuation/integration-r5'); K=C.parent/'kernel'; V=P/'kernel-cpuset-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
manifest=json.loads((C/'manifest.json').read_text());assert sha(C/'Image.gz-dtb')==manifest['image']['sha256'];assert sha(C/'resolved.config')==manifest['config_sha256']
old=json.loads((P/'evidence/firstboot-source-equivalence.json').read_text());paths={row['path'] for row in old['files']}|{'fs/locks.c','include/linux/fs.h'}
sources=[{'path':p,'r7_source_sha256':sha(V/p),'combined_source_sha256':sha(K/p)} for p in sorted(paths)]
for row in sources:assert row['r7_source_sha256']==row['combined_source_sha256'],row
selected={row['option'] for row in json.loads((R/'evidence/firstboot-config-equivalence-r3.json').read_text())['options']}|{'CONFIG_MANDATORY_FILE_LOCKING'}
v=cfg(P/'kernel-build-r7/.config');c=cfg(C/'resolved.config');configs=[{'option':k,'r7':v.get(k,'n'),'combined':c.get(k,'n')} for k in sorted(selected)]
for row in configs:assert row['r7']==row['combined'],row
whole_delta=[{'option':k,'r7':v.get(k,'n'),'combined':c.get(k,'n')} for k in sorted(v.keys()|c.keys()) if v.get(k,'n')!=c.get(k,'n')]
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'combined_manifest_sha256':sha(C/'manifest.json'),'combined_image':manifest['image'],'combined_config_sha256':sha(C/'resolved.config'),'r7_image_sha256':sha(P/'kernel-build-r7/arch/arm64/boot/Image'),'r7_config_sha256':sha(P/'kernel-build-r7/.config'),'sources':sources,'selected_config':configs,'all_selected_equal':True,'whole_config_delta':whole_delta,'whole_kernel_equivalent':False,'combined_kernel_executed':False,'limit':'Selected firstboot source and configuration parity only; combined includes untested network/radio changes and physical board drivers; virtual GIC guard remains fixture-only.'}
(R/'evidence/combined-parity.json').write_text(json.dumps(receipt,indent=2));print('source equality',len(sources),'config equality',len(configs),'whole config differences',len(whole_delta))
