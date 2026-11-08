from pathlib import Path
import os,json,hashlib,tarfile,shutil,subprocess,datetime,gzip
R=Path('/srv/android/asus-bmc156-full-kernel-r1');B=Path('/srv/android/asus-build-continuation');A=Path('/srv/android/asus-bmc156-accelerometer-r1')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def tree(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file() and not f.is_symlink()}
assert R.parent.resolve()==Path('/srv/android') and not R.exists() and not R.is_symlink()
assert shutil.disk_usage(R.parent).free>40*1024**3
snap=json.loads((B/'evidence/snapshot.json').read_text());rec=json.loads((B/'integration-r5/source-receipt.json').read_text())
assert sha(B/'evidence/snapshot.json')=='e219c0e87d2cfca252088e06839dbf9cedaa794b3832e3829cf5c96021717315'
assert sha(B/'integration-r5/source-receipt.json')=='b207be8fcb6739202fae31f54a987f2d11834d43f618edd2a47c6cc33fe2ebe4'
assert sha(B/'inputs/active-soc-source.tar.gz')==snap['archive_sha256']
assert sha(B/'integration-r5/combined-source-changes.tar.gz')==rec['source_archive_sha256']
assert sha(B/'integration-r5/combined-from-active-soc.patch')==rec['patch_sha256']
assert sha(B/'build/.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f'
assert sha(B/'build/arch/arm64/boot/Image.gz-dtb')=='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401'
assert sha(A/'patches/kernel-from-physical-r5.patch')=='1f40942ee014bda87c4e4c382b881e27c98b2034b227a06020a7e96126399cec'
R.mkdir();K=R/'kernel'
for n in ['kernel','out','evidence','patches','scripts','tmp']:(R/n).mkdir()
(R/'README.md').write_text('Owned BMC156 complete physical kernel BUILD FIXTURE. Independent archive reconstruction; parent sources and products frozen. Inspect evidence/build-status.json before continuing; do not restart on timeout.\n')
save(R/'evidence/preflight.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prefix=str(R),source=str(K),output=str(R/'out'),disk_free=shutil.disk_usage(R).free,affinity=sorted(os.sched_getaffinity(0)),baseline_archive_sha256=snap['archive_sha256'],combined_archive_sha256=rec['source_archive_sha256']))
def extract(p,expected):
 with tarfile.open(p) as t:
  members=t.getmembers();assert {m.name for m in members}==set(expected)
  for m in members:
   assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
   dst=K/m.name;assert dst.resolve().is_relative_to(K)
   dst.parent.mkdir(parents=True,exist_ok=True)
   with t.extractfile(m) as src,dst.open('wb') as out:shutil.copyfileobj(src,out)
   dst.chmod(m.mode)
extract(B/'inputs/active-soc-source.tar.gz',snap['files'])
assert tree(K)==snap['files'];print('BASE VERIFIED',len(snap['files']),flush=True)
for p,v in rec['changes'].items():assert (sha(K/p) if (K/p).exists() else None)==v['before'],p
extract(B/'integration-r5/combined-source-changes.tar.gz',rec['changes'])
expected=dict(snap['files']);expected.update({p:v['after'] for p,v in rec['changes'].items()})
assert tree(K)==expected
baseline=json.loads((A/'evidence/baseline-source-hashes.json').read_text());assert expected==baseline
assert tree(B/'kernel')==baseline
manifest=json.loads((A/'patches/pre-post-hashes.json').read_text())
# Use original checker for both exact preimages and postimages.
shutil.copyfile(A/'patches/kernel-from-physical-r5.patch',R/'patches/kernel-from-physical-r5.patch')
shutil.copyfile(A/'patches/pre-post-hashes.json',R/'patches/pre-post-hashes.json')
shutil.copyfile(A/'scripts/check_preimages.py',R/'scripts/check_preimages.py')
subprocess.run(['python3',str(R/'scripts/check_preimages.py'),str(K)],check=True)
cmd=['git','apply','--verbose','--whitespace=nowarn',str(R/'patches/kernel-from-physical-r5.patch')]
p=subprocess.run(cmd,cwd=K,capture_output=True,text=True);(R/'evidence/patch-apply.log').write_text(p.stdout+p.stderr);assert p.returncode==0
assert 'offset' not in p.stderr.lower() and 'fuzz' not in p.stderr.lower()
subprocess.run(['python3',str(R/'scripts/check_preimages.py'),str(K),'--post'],check=True)
final=json.loads((A/'evidence/final-verification.json').read_text());post=dict(baseline);post.update({p:v['after'] for p,v in final['source_changes'].items()});assert tree(K)==post
with gzip.GzipFile(str(R/'evidence/r5-source-manifest.json.gz'),'wb',mtime=0) as f:f.write(json.dumps(baseline,sort_keys=True).encode())
with gzip.GzipFile(str(R/'evidence/post-source-manifest.json.gz'),'wb',mtime=0) as f:f.write(json.dumps(post,sort_keys=True).encode())
for src,name in [(B/'build/.config','physical-r5.config'),(B/'integration-r5/source-receipt.json','r5-source-receipt.json'),(B/'integration-r5/dt-receipt.json','r5-dt-receipt.json'),(B/'integration-r5/config-receipt.json','r5-config-receipt.json'),(B/'integration-r5/runtime-source-preservation.json','r5-runtime-source-preservation.json'),(Path('/srv/android/asus-firstboot-parity-continuation/evidence/combined-parity.json'),'firstboot-combined-parity.json')]:shutil.copyfile(src,R/'evidence'/name)
shutil.copyfile(B/'build/.config',R/'out/.config')
save(R/'evidence/reconstruction.json',dict(base_files=len(snap['files']),combined_delta=len(rec['changes']),r5_files=len(baseline),post_files=len(post),accelerometer_changes=final['source_changes'],original_source_unchanged=True,archive_preimages_postimages_verified=True,source_hardlinks=False,no_fuzz=True,base_commit=rec['base_commit']))
print('READY',R,flush=True)
