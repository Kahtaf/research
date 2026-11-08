from pathlib import Path
import os,resource,json,hashlib,gzip,shutil,tarfile,io,base64,subprocess,signal,time
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
signal.alarm(240)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
os.nice(10)
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1')
B=Path('/srv/android/asus-bmc156-full-kernel-r1')
assert not R.exists() and not R.is_symlink()
status=json.loads((B/'evidence/build-status.json').read_text())
assert status['status']=='complete' and status['exit']==0
manifest=json.loads(gzip.decompress((B/'evidence/post-source-manifest.json.gz').read_bytes()))
assert hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()=='c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'out/.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
size=sum((B/'kernel'/n).stat().st_size for n in manifest)
assert size<3*1024**3 and shutil.disk_usage(B.parent).free>4*1024**3
R.mkdir()
for n in ['kernel','out','evidence','scripts','tmp']:(R/n).mkdir()
(R/'README.md').write_text('Independent GPIO28 source-port review ONLY; owned copies and affected objects/DTB. No hardware, full kernel, integration or image. Read evidence receipts; preserve failures.\n')
for n,h in manifest.items():
    p=B/'kernel'/n;q=R/'kernel'/n
    assert not p.is_symlink() and p.is_file() and sha(p)==h
    assert not Path(n).is_absolute() and '..' not in Path(n).parts
    q.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,q);shutil.copymode(p,q)
    assert sha(q)==h and p.stat().st_ino!=q.stat().st_ino
(R/'evidence/baseline-source-manifest.json').write_text(json.dumps(manifest,sort_keys=True))
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(PAYLOAD)),mode='r:gz') as t:
    for m in t.getmembers():
        assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        assert m.isfile() or m.isdir()
        if m.isdir():(R/m.name).mkdir(parents=True,exist_ok=True)
        else:
            p=R/m.name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(t.extractfile(m).read())
pins=json.loads((R/'inputs/evidence/pre-post-pins.json').read_text())
shutil.copyfile(B/'out/.config',R/'kernel/resolved.config')
for v in pins:
    p=R/'kernel'/v['path']
    assert (sha(p) if p.exists() else None)==v['pre_sha256']
    if v['destination_must_be_absent']:assert not p.exists()
for patch in ['kernel-source.patch','resolved-config.patch']:
    p=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'inputs/patches'/patch)],cwd=R/'kernel',capture_output=True,text=True,timeout=30)
    (R/'evidence'/('apply-'+patch+'.log')).write_text(p.stdout+p.stderr)
    assert p.returncode==0 and 'offset' not in (p.stdout+p.stderr).lower(),p.stdout+p.stderr
for v in pins:assert sha(R/'kernel'/v['path'])==v['post_sha256']
shutil.copyfile(R/'kernel/resolved.config',R/'out/.config')
tools={}
for name,path,expected in [('aarch64-linux-gnu-gcc','/usr/bin/aarch64-linux-gnu-gcc-13','cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a'),('aarch64-linux-gnu-ld','/usr/bin/aarch64-linux-gnu-ld.bfd','7c903ac277dd1f5c4397277db865f12d8239fe45782f71afbeb3d42180a4b1ae'),('gcc','/usr/bin/x86_64-linux-gnu-gcc-13','1b99826121ae6682a634e5efe09bd3e3df58ce58e0b28f849114ab5b89139c26'),('make','/usr/bin/make','d78b8f1d099fbcfb6f2f49ab87223b9b68fb3956642f92d6ec6de812e8afa965')]:
    assert sha(Path(path))==expected
    tools[name]=dict(path=path,sha256=expected,version=subprocess.check_output([name,'--version'],text=True).splitlines()[0])
r=dict(source_files=len(manifest),source_bytes=size,baseline_manifest_sha256='c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124',all_preimages_postimages_verified=True,patch_fuzz=0,hardlinks=False,cpu_affinity=sorted(os.sched_getaffinity(0)),address_space_bytes=resource.getrlimit(resource.RLIMIT_AS),owned_storage_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),toolchains=tools)
assert r['owned_storage_bytes']<4*1024**3
(R/'evidence/initialization.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
