from pathlib import Path
import os,json,hashlib,subprocess as s,datetime,time
R=Path('/srv/android/asus-android-runtime-network-parity-20261107');E=R/'evidence';S=R/'kernel';B=R/'build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
pins=json.loads((R/'integration/pins.json').read_text());original=Path('/srv/android/asus-firstboot-runtime/kernel-cpuset-r1');config=Path('/srv/android/asus-firstboot-runtime/kernel-build-r7/.config')
assert sha(config)==pins['preserve_android_config_sha256']
assert not S.exists();s.run(['cp','-a','--reflink=auto',str(original),str(S)],check=True)
(B/'.config').write_bytes(config.read_bytes());(E/'original.config').write_bytes(config.read_bytes())
pre={n:sha(S/n) if (S/n).exists() else None for n in pins['combined_pre']};assert pre==pins['combined_pre'],pre
patches=[]
for n in pins['qualified_follow_on_order']:
 p=R/'integration'/n;assert sha(p)==pins['patch_sha256'][n]
 x=s.run(['patch','--batch','--fuzz=0','-p1','-i',str(p)],cwd=S,capture_output=True,text=True)
 patches.append(dict(patch=n,sha256=sha(p),exit=x.returncode,stdout=x.stdout,stderr=x.stderr));(E/'patch-application.json').write_text(json.dumps(patches,indent=2))
 assert x.returncode==0 and 'offset' not in x.stdout.lower() and 'fuzz' not in x.stdout.lower(),x.stdout+x.stderr
post={n:sha(S/n) for n in pins['combined_post']};assert post==pins['combined_post']
d=dict(source_origin=str(original),source_copy=str(S),build_origin_config=str(config),output=str(B),pre=pre,post=post,exact_five_postimages=True,patches=patches,config_before=sha(B/'.config'),full_config_preserved=True,full_tree_hash_not_run=True)
(E/'integration.json').write_text(json.dumps(d,indent=2))
cmd=['make','-C',str(S),'O='+str(B),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','-j8','Image']
env=os.environ.copy();env.update(KBUILD_BUILD_USER='asus-port',KBUILD_BUILD_HOST='runtime-network-parity',KBUILD_BUILD_TIMESTAMP='Sat Nov 7 00:00:00 UTC 2026',TMPDIR=str(R/'tmp'))
status=dict(started_utc=now(),command=cmd,compile_invocations=1,rlimit_as_added=False,config_before=sha(B/'.config'));(E/'build-started.json').write_text(json.dumps(status,indent=2));start=time.monotonic()
with (E/'build.log').open('wb') as f:
 p=s.Popen(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,env=env);status['owned_make_pid']=p.pid;(E/'build-started.json').write_text(json.dumps(status,indent=2));status['returncode']=p.wait()
status.update(finished_utc=now(),elapsed_wall_seconds=time.monotonic()-start,config_after=sha(B/'.config'),five_postimages_after={n:sha(S/n) for n in pins['combined_post']})
status['full_config_preserved']=status['config_after']==pins['preserve_android_config_sha256'];status['exact_five_postimages']=status['five_postimages_after']==pins['combined_post']
if status['returncode']==0:
 image=B/'arch/arm64/boot/Image';status.update(image_sha256=sha(image),image_bytes=image.stat().st_size)
 (E/'built.config').write_bytes((B/'.config').read_bytes())
status['genuine_build_success']=status['returncode']==0 and status['full_config_preserved'] and status['exact_five_postimages']
(E/'build-result.json').write_text(json.dumps(status,indent=2))
