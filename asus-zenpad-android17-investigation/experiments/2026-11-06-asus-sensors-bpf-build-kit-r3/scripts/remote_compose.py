from pathlib import Path
import base64,datetime,difflib,gzip,hashlib,json,os,resource,shutil,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));os.nice(10)
OLD=Path('/srv/android/asus-product-integration-staging/r2');NEW=Path('/srv/android/asus-product-integration-staging/r3')
KIT=Path('/srv/android/asus-reviewed-build-kit/r2');ACTIVE=Path('/srv/android/lineage24');K=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel');OUT=K.parent/'out'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def need(b,s):
 if not b:raise RuntimeError(s)
def item(p):return {'symlink':os.readlink(p)} if p.is_symlink() else {'sha256':sha(p)}
def manifest(root):return {str(p.relative_to(root)):item(p) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')
need(not NEW.exists(),'r3 staging prefix exists; refuse overwrite')
need(not Path('/srv/android/asus-reviewed-build-kit/r3').exists(),'r3 kit prefix unexpectedly exists')
need(sha(KIT/'inputs/kit-pins.json')=='841581a33251c975d19329d03318fb1e43e94dbdfebddcac4cd7d1def742ad70','r2 seal mismatch')
for rel,h in json.loads((KIT/'inputs/kit-pins.json').read_text()).items():need(sha(KIT/rel)==h,'r2 kit drift '+rel)
need(sha(OLD/'STAGED.json')=='e6550c455d994932180c0f254dc84a0cd51838274dfe0fe66b82522cf3edc213','r2 staging receipt mismatch')
r2=json.loads((OLD/'STAGED.json').read_text());old_all=manifest(OLD)
need(manifest(OLD/'product-device')==r2['product_after'],'r2 product drift')
need(manifest(ACTIVE/'device/asus/p00a')==r2['product_before'],'active product drift')
NEW.mkdir()
try:
 for name in ['product-device','platform-connectivity','kernel-config','full-boot-tools']:shutil.copytree(OLD/name,NEW/name,symlinks=True)
 evidence=NEW/'composition';evidence.mkdir()
 for rel,b64 in PAYLOAD.items():
  p=evidence/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b64))
 pins=json.loads((evidence/'inputs/bmc156-source-pins.json').read_text())
 newconfig=OUT/'.config';newimage=OUT/'arch/arm64/boot/Image.gz-dtb'
 need(sha(newconfig)==pins['config_sha256']=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2','new config mismatch')
 need(sha(newimage)==pins['image_sha256']=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1' and newimage.stat().st_size==7716897,'new physical image mismatch')
 need(sha(OUT/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb')==pins['dtb_sha256']=='a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77','DT mismatch')
 delta=json.loads((evidence/'inputs/bmc156-pre-post.json').read_text())
 prior=json.loads((KIT/'inputs/source-receipt.json').read_text());baseline=json.loads((KIT/'inputs/snapshot.json').read_text())
 post=gzip.decompress((K.parent/'evidence/post-source-manifest.json.gz').read_bytes());complete=json.loads(post)
 r5=json.loads(gzip.decompress((K.parent/'evidence/r5-source-manifest.json.gz').read_bytes()))
 expected=dict(r5)
 for rel,d in delta.items():need(r5.get(rel)==d['before'],'BMC r5 preimage mismatch');expected[rel]=d['after']
 need(expected==complete and len(delta)==9,'Complete BMC source manifest mismatch')
 changes={rel:{'before':baseline['files'].get(rel),'after':h} for rel,h in complete.items() if h!=baseline['files'].get(rel)}
 need(len(changes)==276 and set(changes)==set(prior['changes'])|set(delta),'276 source selection mismatch')
 active_kernel=Path(baseline['source']);fixture=NEW/'source-patch-fixture';fixture.mkdir()
 lines=[]
 for rel,entry in sorted(changes.items()):
  before=(active_kernel/rel).read_bytes() if entry['before'] else b'';after=(K/rel).read_bytes()
  need((hashlib.sha256(before).hexdigest() if entry['before'] else None)==entry['before'],'Original preimage mismatch '+rel)
  need(hashlib.sha256(after).hexdigest()==entry['after'],'Physical compiled postimage mismatch '+rel)
  if entry['before']:
   q=fixture/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(before)
  lines.append(('diff --git a/'+rel+' b/'+rel+'\n').encode())
  if not entry['before']:lines.append(b'new file mode 100644\n')
  for line in difflib.diff_bytes(difflib.unified_diff,before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile=('a/'+rel if entry['before'] else '/dev/null').encode(),tofile=('b/'+rel).encode()):
   lines.append(line if line.endswith(b'\n') else line+b'\n\\ No newline at end of file\n')
 patch=NEW/'kernel-source/combined-from-original.patch';patch.parent.mkdir();patch.write_bytes(b''.join(lines))
 subprocess.run(['git','-C',str(fixture),'apply','--check','--whitespace=nowarn',str(patch)],check=True,capture_output=True)
 subprocess.run(['git','-C',str(fixture),'apply','--whitespace=nowarn',str(patch)],check=True,capture_output=True)
 need(all(sha(fixture/rel)==d['after'] for rel,d in changes.items()),'Exact combined patch reconstruction mismatch')
 source={'base_commit':baseline['head'],'changes':changes,'patch_sha256':sha(patch),'active_source_files_verified':61976,'bmc156_r5_relative_patch_sha256':sha(evidence/'inputs/bmc156-from-r5.patch'),'parent_r2_source_receipt_sha256':sha(KIT/'inputs/source-receipt.json'),'complete_compiled_manifest_sha256':hashlib.sha256(post).hexdigest(),'compiled_kernel_sha256':sha(newimage),'config_sha256':sha(newconfig),'physical_executed':False}
 write(NEW/'kernel-source/source-receipt.json',source)
 shutil.copy2(K.parent/'evidence/post-source-manifest.json.gz',NEW/'kernel-source/complete-postimages.json.gz')
 shutil.copy2(K.parent/'evidence/full-verification.json',NEW/'kernel-source/full-verification.json')
 shutil.copy2(OUT/'include/config/kernel.release',NEW/'kernel-source/kernel.release')
 shutil.copy2(newimage,NEW/'product-device/prebuilt/Image.gz-dtb');shutil.copy2(newconfig,NEW/'kernel-config/asus_p00a_combined_defconfig')
 sensor=NEW/'product-device/sensors';shutil.copytree(evidence/'inputs/sensor-source',sensor)
 original_sensor=manifest(sensor)
 mk=(sensor/'sensors.mk').read_bytes()
 for name in [b'android.hardware.sensors@1.0-service',b'android.hardware.sensors@1.0-impl']:
  need(mk.count(name)==1,'Sensor module occurrence mismatch');mk=mk.replace(name,name+b':64')
 (sensor/'sensors.mk').write_bytes(mk)
 suffixes={'device.mk':'\n$(call inherit-product, device/asus/p00a/sensors/sensors.mk)\n','BoardConfig.mk':'\ninclude device/asus/p00a/sensors/BoardConfig.mk\n','rootdir/ueventd.rc':'\n'+'\n'.join(l for l in (sensor/'ueventd.fragment.rc').read_text().splitlines() if l and not l.startswith('#'))+'\n'}
 need(len(suffixes['rootdir/ueventd.rc'].strip().splitlines())==5,'Wrong ueventd addition')
 bases={}
 for rel,suffix in suffixes.items():
  base=(OLD/'product-device'/rel).read_bytes();bases[rel]=base64.b64encode(base).decode();(NEW/'product-device'/rel).write_bytes(base+suffix.encode())
 sensor_receipt={'original_files':original_sensor,'files':manifest(sensor),'suffixes':suffixes,'base_sha256':{p:r2['product_after'][p]['sha256'] for p in suffixes},'after_sha256':{p:sha(NEW/'product-device'/p) for p in suffixes},'architecture_adjustment':'Only add :64 suffix to the two genuine SDK37 HIDL package names; supported by actual build/make/core/main.mk','calibration_payload_included':False,'physical_sensor_qualified':False}
 write(NEW/'sensor-selection.json',sensor_receipt)
 platform_receipts={}
 for name,root,rel,before,after,patchname,file in [
  ('platform_bpf',ACTIVE/'system/bpf','loader/bpfloader.rs','1548dffa03b5091bbb9b7cfcce92495ee2167f417e90b431117cf31ea77b4bd2','babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250','platform-bpf.patch','bpfloader.rs'),
  ('vold',ACTIVE/'system/vold','model/PublicVolume.cpp','0e17fccedefabb20e2d8650252af8c765af68378a1d853e0fbaa6a8bd1ea67fd','c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9','vold.patch','PublicVolume.cpp')]:
  need(sha(root/rel)==before and sha(evidence/'inputs'/file)==after,'Platform source pin mismatch '+name)
  staged_root=NEW/('platform-bpf' if name=='platform_bpf' else 'platform-vold');dest=staged_root/rel;dest.parent.mkdir(parents=True);shutil.copy2(evidence/'inputs'/file,dest)
  f=NEW/('patch-check-'+name)/rel;f.parent.mkdir(parents=True);shutil.copy2(root/rel,f)
  subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(evidence/'inputs'/patchname)],cwd=f.parents[len(Path(rel).parts)-1],check=True,capture_output=True)
  need(sha(f)==after,'Exact patch application failed '+name)
  receipt={'root':str(root),'files':{rel:{'before':before,'after':after}},'staged_root':str(staged_root),'patch_sha256':sha(evidence/'inputs'/patchname),'native_product_rebuild_required':True,'fixture_binary_is_shipping_input':False}
  if name=='vold':need(dest.read_bytes().replace(b'#include <algorithm>\n',b'',1)==(root/rel).read_bytes(),'vold fix is not only algorithm include')
  write(NEW/(name+'-receipt.json'),receipt);platform_receipts[name]=receipt
 after=manifest(NEW/'product-device');changed={p for p in after.keys()|r2['product_after'].keys() if after.get(p)!=r2['product_after'].get(p)}
 need(changed=={'prebuilt/Image.gz-dtb',*suffixes}|{'sensors/'+p for p in sensor_receipt['files']},'Unintended r3 product delta')
 staged=dict(r2);staged.update(path=str(NEW),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),product_after=after,kernel_config_path=str(NEW/'kernel-config/asus_p00a_combined_defconfig'),kernel_config_sha256=sha(newconfig),parent_r2_staged_sha256=sha(OLD/'STAGED.json'),sensor_selection=sensor_receipt,platform_bpf=platform_receipts['platform_bpf'],vold=platform_receipts['vold'],source_receipt_sha256=sha(NEW/'kernel-source/source-receipt.json'),parent_parity_receipt_sha256=sha(evidence/'inputs/firstboot-parent-acceptance.json'),firstboot_parity_accepted=False,physical_boot_verified=False,full_product_ready=False)
 staged['handoff_pins']=dict(staged['handoff_pins']);staged['handoff_pins'].update({'Image.gz-dtb':sha(newimage),'resolved.config':sha(newconfig)})
 write(NEW/'STAGED.json',staged)
 need(manifest(OLD)==old_all,'Frozen r2 staging mutated')
 need(manifest(ACTIVE/'device/asus/p00a')==r2['product_before'],'Active product mutated')
 exports={}
 for src,rel in [(NEW/'STAGED.json','inputs/STAGED.json'),(NEW/'sensor-selection.json','inputs/sensor-selection.json'),(NEW/'kernel-source/source-receipt.json','inputs/source-receipt.json'),(NEW/'kernel-source/full-verification.json','inputs/actual-kernel-contract.json'),(NEW/'kernel-source/kernel.release','inputs/kernel.release'),(NEW/'kernel-source/complete-postimages.json.gz','inputs/complete-kernel-postimages.json.gz')]+[(NEW/(n+'-receipt.json'),'inputs/'+n+'-receipt.json') for n in platform_receipts]:exports[rel]=base64.b64encode(src.read_bytes()).decode()
 for rel,data in bases.items():exports['inputs/r2-product/'+rel]=data
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'staged_sha256':sha(NEW/'STAGED.json'),'source_patch_sha256':sha(patch),'sensor_source_files':len(original_sensor),'kernel_distinct_changes':276,'r2_product_differences':sorted(changed),'old_r2_staging_unchanged':True,'active_product_unchanged':True,'no_active_source_writes':True,'full_build_started':False,'exports':exports}
 write(NEW/'composition/receipt.json',{k:v for k,v in result.items() if k!='exports'})
 print(json.dumps(result))
except BaseException as e:
 write(NEW/'COMPOSITION-FAILED.json',{'error':str(e),'retry_without_review':False});raise
