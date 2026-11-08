"""Rebind only the new kit/candidate; retain immutable original handoffs as ancestors."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];oldkit='/srv/android/asus-reviewed-build-kit/r2';kit='/srv/android/asus-reviewed-build-kit/r3';oldstage='/srv/android/asus-product-integration-staging/r2';stage='/srv/android/asus-product-integration-staging/r3';A='/srv/android/lineage24';K='/srv/android/asus-bmc156-full-kernel-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def paths(v):
 if isinstance(v,str):return v.replace(oldkit,kit).replace(oldstage,stage)
 if isinstance(v,list):return [paths(x) for x in v]
 if isinstance(v,dict):return {paths(k):paths(x) for k,x in v.items()}
 return v
p=paths(read(R.parent/'2026-11-06-asus-product-input-build-kit/inputs/plan.json'))
s=read(R/'inputs/STAGED.json');src=read(R/'inputs/source-receipt.json')
p.update(run_root=kit,staging=stage,patch=stage+'/kernel-source/combined-from-original.patch',compiled_fixture=K+'/kernel',kernel_release=stage+'/kernel-source/kernel.release',previous_staged_receipt=kit+'/inputs/r2-STAGED.json',previous_source_receipt=kit+'/inputs/r2-source-receipt.json',previous_product_inputs=kit+'/inputs/r2-product',kernel_delta=kit+'/inputs/bmc156-pre-post.json',complete_kernel_manifest=kit+'/inputs/complete-kernel-postimages.json.gz',sensor_receipt=kit+'/inputs/sensor-selection.json',sensor_origin=kit+'/inputs/sensor-source',bpf_supplement_manifest=kit+'/inputs/bpf-supplement-manifest.json',bpf_supplement_archive=kit+'/inputs/bpf-supplement.tar.gz',bpf_qualified_selection=kit+'/inputs/bpf-qualified-selection.json',production_build_jobs=8)
for name,sub,root in [('platform_bpf','platform-bpf','system/bpf'),('vold','platform-vold','system/vold')]:
 p[name]=A+'/'+root;p[name+'_staged']=stage+'/'+sub;p[name+'_receipt']=kit+'/inputs/'+name+'-receipt.json'
external=p['external_pins']
for rel,expected in [('STAGED.json',sha(R/'inputs/STAGED.json')),('product-device/prebuilt/Image.gz-dtb',s['handoff_pins']['Image.gz-dtb']),('kernel-config/asus_p00a_combined_defconfig',s['kernel_config_sha256']),('kernel-source/source-receipt.json',sha(R/'inputs/source-receipt.json')),('kernel-source/combined-from-original.patch',src['patch_sha256']),('kernel-source/full-verification.json',sha(R/'inputs/actual-kernel-contract.json')),('kernel-source/complete-postimages.json.gz',sha(R/'inputs/complete-kernel-postimages.json.gz')),('kernel-source/kernel.release',sha(R/'inputs/kernel.release'))]:external[stage+'/'+rel]=expected
for rel,item in s['product_after'].items():
 if 'sha256' in item:external[stage+'/product-device/'+rel]=item['sha256']
for name in ['platform_bpf','vold']:
 receipt=read(R/'inputs'/f'{name}-receipt.json');external[stage+'/'+name+'-receipt.json']=sha(R/'inputs'/f'{name}-receipt.json')
 for rel,row in receipt['files'].items():external[p[name+'_staged']+'/'+rel]=row['after']
external[stage+'/sensor-selection.json']=sha(R/'inputs/sensor-selection.json')
external[oldkit+'/inputs/kit-pins.json']=sha(R/'inputs/r2-kit-pins.json')
for rel,digest in read(R/'inputs/r2-kit-pins.json').items():external[oldkit+'/'+rel]=digest
external[oldstage+'/STAGED.json']=sha(R/'inputs/r2-STAGED.json')
external[K+'/out/.config']=s['kernel_config_sha256'];external[K+'/out/arch/arm64/boot/Image.gz-dtb']=s['handoff_pins']['Image.gz-dtb']
for doc in ['initial-remote.json','build-mechanisms.json']:
 d=read(R/'evidence'/doc);rows=d.get('source',d)
 for rel,entry in rows.items():
  if isinstance(entry,dict) and 'sha256' in entry and not rel.startswith('device/asus/p00a/'):
   external[A+'/'+rel]=entry['sha256']
# Current originals are future write destinations, not immutable post-build inputs.
for rel in ['system/bpf/loader/bpfloader.rs','system/vold/model/PublicVolume.cpp']:
 external.pop(A+'/'+rel,None)
p['parent_contract']='PLAN_ONLY default; r5 failed: exact hash-bound parent failure review required before one-shot r6 integration/build. No physical GO.'
p['r3_hardware_status']={'accelerometer_physical_qualified':False,'calibration_restoration_parent_only':True,'camera_working_provider':False,'audio_working_route':False,'platform_bpf_property_service_runtime':False}
(R/'inputs/plan.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
print('r3 plan external pins',len(external))
