import os,pathlib,hashlib,json,resource,signal
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/asus-r9-actual-system-mount-20261106');options=['CONFIG_ARM64_4K_PAGES','CONFIG_64BIT','CONFIG_EXT4_FS','CONFIG_EXT4_FS_SECURITY','CONFIG_EXT4_FS_POSIX_ACL','CONFIG_EXT4_ENCRYPTION'];d={}
for name,path in [('virtual','/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/out/.config'),('physical','/srv/android/asus-bmc156-full-kernel-r1/out/.config')]:
 p=P(path);b=p.read_bytes();lines=b.decode().splitlines();vals={k:next((s.split('=',1)[1]for s in lines if s.startswith(k+'=')),'n')for k in options};d[name]=dict(path=path,sha256=hashlib.sha256(b).hexdigest(),selected_options=vals)
assert d['virtual']['sha256']=='0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f'
assert d['virtual']['selected_options']==d['physical']['selected_options']
p=P('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source/fs/ext4/ext4.h');b=p.read_bytes();text=b.decode();start=text.index('#define EXT4_FEATURE_COMPAT_SUPP');end=text.index('\n\n',text.index('#define EXT4_FEATURE_RO_COMPAT_SUPP'))
d['current_ext4_header']=dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),support_definitions=text[start:end])
d['owned_final_bytes']=sum(p.stat().st_size for p in R.rglob('*')if p.is_file());assert d['owned_final_bytes']<128*1024**2
p=R/'run/result.json';d['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();d['no_additional_raw_hash']=True
(R/'seal.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
