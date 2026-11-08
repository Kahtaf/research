from pathlib import Path
import os,resource,signal,json,hashlib,subprocess,shutil
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90));signal.alarm(180)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');K=R/'kernel';E=R/'evidence'
assert not (E/'initialization.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((R/'inputs/evidence/pre-post-pins.json').read_text())
for v in pins:
 if v['path']!='resolved.config':assert sha(K/v['path'])==v['post_sha256']
assert sha(K/'resolved.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
D=R/'config-replay';D.mkdir();shutil.move(K/'resolved.config',D/'.config')
p=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'inputs/patches/resolved-config.patch')],cwd=D,capture_output=True,text=True,timeout=30)
(E/'apply-resolved-config-correct-path.log').write_text(p.stdout+p.stderr)
assert p.returncode==0 and 'offset' not in (p.stdout+p.stderr).lower()
assert sha(D/'.config')=='26c59e0afa3f6438fafea4b5379b898c9b1fcaf05adf1d7e14db93b2e976bd13'
shutil.copyfile(D/'.config',R/'out/.config')
tools={}
for name,path,expected in [('aarch64-linux-gnu-gcc','/usr/bin/aarch64-linux-gnu-gcc-13','cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a'),('aarch64-linux-gnu-ld','/usr/bin/aarch64-linux-gnu-ld.bfd','7c903ac277dd1f5c4397277db865f12d8239fe45782f71afbeb3d42180a4b1ae'),('gcc','/usr/bin/x86_64-linux-gnu-gcc-13','1b99826121ae6682a634e5efe09bd3e3df58ce58e0b28f849114ab5b89139c26'),('make','/usr/bin/make','d78b8f1d099fbcfb6f2f49ab87223b9b68fb3956642f92d6ec6de812e8afa965')]:
 assert sha(Path(path))==expected
 tools[name]=dict(path=path,sha256=expected,version=subprocess.check_output([name,'--version'],text=True).splitlines()[0])
manifest=json.loads((E/'baseline-source-manifest.json').read_text());post=dict(manifest)
for v in pins:
 if v['path']!='resolved.config':post[v['path']]=v['post_sha256']
assert all(sha(K/n)==h for n,h in post.items())
(E/'candidate-source-manifest.json').write_text(json.dumps(post,sort_keys=True))
r=dict(source_files=len(manifest),source_bytes=sum((K/n).stat().st_size for n in post),baseline_manifest_sha256='c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124',all_preimages_postimages_verified=True,source_paths_modified=6,config_path_alias='candidate/resolved.config -> isolated config-replay/.config -> out/.config',preserved_failed_config_replay=True,patch_fuzz=0,hardlinks=False,cpu_affinity=sorted(os.sched_getaffinity(0)),address_space_bytes=resource.getrlimit(resource.RLIMIT_AS),owned_storage_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),toolchains=tools)
assert r['owned_storage_bytes']<4*1024**3
(E/'initialization.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
