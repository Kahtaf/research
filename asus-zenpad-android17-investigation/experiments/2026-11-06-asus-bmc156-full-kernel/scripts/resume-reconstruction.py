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
def tree(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file() and not f.is_symlink() and '.git' not in f.relative_to(p).parts}
assert R.resolve()==R and (R/'evidence/preflight.json').exists() and not (R/'evidence/reconstruction.json').exists()
assert shutil.disk_usage(R).free>30*1024**3
K=R/'kernel'
snap=json.loads((B/'evidence/snapshot.json').read_text());rec=json.loads((B/'integration-r5/source-receipt.json').read_text())
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
