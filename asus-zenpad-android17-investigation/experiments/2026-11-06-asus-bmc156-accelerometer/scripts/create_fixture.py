from pathlib import Path
import subprocess,hashlib,json,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1'); B=Path('/srv/android/asus-build-continuation')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not R.exists(), 'unique fixture already exists'
assert sha(B/'build/.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f'
assert sha(B/'build/arch/arm64/boot/Image.gz-dtb')=='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401'
R.mkdir();(R/'evidence').mkdir();(R/'out').mkdir();(R/'source').mkdir();(R/'preimages').mkdir()
subprocess.run(['cp','-a','--reflink=auto',str(B/'kernel'),str(R/'kernel')],check=True)
# No copied repository metadata and no hardlinked regular sources.
import shutil
if (R/'kernel/.git').exists():
 p=R/'kernel/.git';shutil.rmtree(p) if p.is_dir() else p.unlink()
count=0; manifest={}
for p in (R/'kernel').rglob('*'):
 if p.is_file() and not p.is_symlink():
  rel=str(p.relative_to(R/'kernel')); orig=B/'kernel'/rel
  assert p.stat().st_ino != orig.stat().st_ino
  manifest[rel]=sha(p);count+=1
shutil.copy2(B/'build/.config',R/'out/.config');shutil.copy2(B/'build/.config',R/'evidence/physical-r5.config')
(R/'evidence/baseline-source-hashes.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
(R/'evidence/fixture.json').write_text(json.dumps({'base':str(B/'kernel'),'files':count,'hardlinks':False,'config_sha256':sha(R/'out/.config'),'compiled_base_image_sha256':sha(B/'build/arch/arm64/boot/Image.gz-dtb')},indent=2)+'\n')
print('Created',R,'independent files',count)
print(subprocess.run(['df','-h',str(R)],capture_output=True,text=True).stdout)
