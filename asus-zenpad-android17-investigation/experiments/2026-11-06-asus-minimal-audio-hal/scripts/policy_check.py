from pathlib import Path
import subprocess,os,resource,shutil,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out'
p=a/'out/soong/.intermediates/system/sepolicy/precompiled_sepolicy/android_common/p00a/precompiled_sepolicy';dest=out/'policy-baseline';shutil.copyfile(p,dest)
source=a/'system/sepolicy/private/hal_audio.te';lines=source.read_text().splitlines();rules='\n'.join(x for x in lines if x.startswith('neverallow '))+'\n';(out/'audio-neverallows.conf').write_text(rules)
cmd=[str(a/'out/host/linux-x86/bin/sepolicy-analyze'),str(dest),'neverallow','-f',str(out/'audio-neverallows.conf')]
r=subprocess.run(cmd,capture_output=True,text=True)
receipt={'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'policy_source':str(p),'policy_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'rules_source':str(source),'rules':rules,'scope':'Only two actual audio-specific platform neverallows against captured existing policy; no policy delta; NOT full future product validation'}
(out/'neverallow-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
