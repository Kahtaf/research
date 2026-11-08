from pathlib import Path
import json,hashlib,gzip,shutil,difflib,datetime,os
R=Path('/srv/android/asus-bmc156-full-kernel-r1');E=R/'evidence';O=R/'out';X=R/'export'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
verification=json.loads((E/'full-verification.json').read_text());assert verification['full_kernel_compiled']
assert not X.exists();assert shutil.disk_usage(R).free>1024**3
X.mkdir()
for d in ['evidence','artifacts','patches','scripts','source']:(X/d).mkdir()
for n in ['Image.gz-dtb']:
 shutil.copyfile(O/'arch/arm64/boot'/n,X/'artifacts'/n)
shutil.copyfile(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb',X/'artifacts/asus-p00a.dtb')
shutil.copyfile(O/'.config',X/'artifacts/resolved.config')
shutil.copyfile(O/'include/config/kernel.release',X/'artifacts/kernel.release')
for p in sorted(E.iterdir()):
 if p.is_file() and p.suffix in ['.json','.log','.txt','.config'] and p.name not in ['build.lock']:
  dest=X/'evidence'/p.name
  if p.suffix=='.log':
   with gzip.GzipFile(str(dest)+'.gz','wb',mtime=0) as f:f.write(p.read_bytes())
  else:shutil.copyfile(p,dest)
shutil.copyfile(E/'r5-source-manifest.json.gz',X/'evidence/r5-source-manifest.json.gz')
with gzip.GzipFile(str(X/'evidence/System.map.gz'),'wb',mtime=0) as f:f.write((O/'System.map').read_bytes())
for n in ['compile.h','utsrelease.h']:shutil.copyfile(O/'include/generated'/n,X/'evidence'/n)
for p in (R/'patches').iterdir():
 if p.is_file():shutil.copyfile(p,X/'patches'/p.name)
for p in (R/'scripts').iterdir():
 if p.is_file() and p.suffix=='.py':shutil.copyfile(p,X/'scripts'/p.name)
changes=json.loads((R/'patches/pre-post-hashes.json').read_text())
for rel,v in changes.items():
 p=R/'kernel'/rel;assert sha(p)==v['after'];d=X/'source'/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
(X/'patches/resolved-config-from-r5.patch').write_text(''.join(difflib.unified_diff((E/'physical-r5.config').read_text().splitlines(True),(O/'.config').read_text().splitlines(True),fromfile='a/resolved.config',tofile='b/resolved.config')))
recipe=dict(status='FUTURE_PARENT_DELTA_ONLY_NOT_APPLIED',frozen_kit_seal='841581a33251c975d19329d03318fb1e43e94dbdfebddcac4cd7d1def742ad70',kernel_source_base='compiled physical r5; exact original 268-file handoff first',source_patch='patches/kernel-from-physical-r5.patch',source_patch_sha256=sha(X/'patches/kernel-from-physical-r5.patch'),source_pre_post_manifest='patches/pre-post-hashes.json',future_candidate_replacements=[dict(role='product-device/prebuilt/Image.gz-dtb',before_sha256='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401',artifact='artifacts/Image.gz-dtb',after_sha256=sha(X/'artifacts/Image.gz-dtb')),dict(role='kernel-config/asus_p00a_combined_defconfig (complete resolved config)',before_sha256='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f',artifact='artifacts/resolved.config',after_sha256=sha(X/'artifacts/resolved.config'))],kernel_release=(O/'include/config/kernel.release').read_text().strip(),regenerate_future_candidate_receipts=['combined source receipt/archive/patch incorporating nine extra source paths','image/config/DT/header/layout manifest','product staged receipt and external input pins and kit seal'],hal_product_delta_applied=False,remaining=['HAL source and ARM64 sensors service Soong integration','init/ueventd/policy/VINTF/ELF full-product verification','private original calibration restoration by parent','physical sensor and autorotation qualification'],physical_claims=False)
(X/'parent-delta.json').write_text(json.dumps(recipe,indent=2)+'\n')
manifest={str(p.relative_to(X)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in X.rglob('*') if p.is_file()}
size=sum(v['bytes'] for v in manifest.values());assert size<12*1024**2,size
(X/'MANIFEST.json').write_text(json.dumps(dict(files=manifest,total_bytes=size,created=datetime.datetime.now(datetime.timezone.utc).isoformat()),sort_keys=True,indent=2)+'\n')
print('EXPORT',len(manifest),'files',size,'bytes',sha(X/'MANIFEST.json'))
