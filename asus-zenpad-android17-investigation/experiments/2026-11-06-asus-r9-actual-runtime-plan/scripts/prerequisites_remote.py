import os,pathlib,json,hashlib,resource,signal,zipfile
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;c=P('/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/config').read_text().splitlines();keys=['CONFIG_COMPAT','CONFIG_BINFMT_ELF','CONFIG_BLK_DEV_LOOP','CONFIG_BLK_DEV_DM','CONFIG_DM_VERITY','CONFIG_DM_CRYPT','CONFIG_EXT4_FS','CONFIG_EROFS_FS','CONFIG_SECURITY_SELINUX','CONFIG_SECURITY_SELINUX_DEVELOP','CONFIG_KEYS','CONFIG_CRYPTO_SHA256','CONFIG_CRYPTO_SHA512','CONFIG_CRYPTO_RSA','CONFIG_CRYPTO_AES','CONFIG_CRYPTO_XTS','CONFIG_FILE_LOCKING','CONFIG_CPUSETS','CONFIG_BLK_CGROUP'];d={'runtime_kernel_options':{k:next((s.split('=',1)[1]for s in c if s.startswith(k+'=')),'n')for k in keys}}
p=P('/srv/android/lineage24/out/target/product/p00a/system/apex/com.android.runtime.apex');d['runtime_apex']={'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
with zipfile.ZipFile(p)as z:
 d['runtime_apex']['members']=[dict(name=i.filename,bytes=i.file_size,compression=i.compress_type)for i in z.infolist()]
 pub=z.read('apex_pubkey');d['runtime_apex']['embedded_public_key_sha256']=hashlib.sha256(pub).hexdigest()
 with z.open('apex_payload.img')as f:sb=f.read(2048)
 d['runtime_apex']['payload_filesystem']='ext4'if sb[1080:1082]==bytes.fromhex('53ef')else'erofs'if sb[1024:1028]==bytes.fromhex('e2e1f5e0')else'unknown'
print(json.dumps(d,indent=2))
