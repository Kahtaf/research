from pathlib import Path
import subprocess,os,resource,shutil,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out';root=a/'out/soong/.intermediates/system/sepolicy';copies=out/'policy-inputs';copies.mkdir(exist_ok=True)
rels=['plat_sepolicy.cil/android_common/plat_sepolicy.cil','plat_mapping_file/android_common/202704.cil','system_ext_sepolicy.cil/android_common/p00a/system_ext_sepolicy.cil','system_ext_mapping_file/android_common/p00a/202704.cil','product_sepolicy.cil/android_common/p00a/product_sepolicy.cil','product_mapping_file/android_common/p00a/202704.cil','plat_pub_versioned.cil/android_common/p00a/plat_pub_versioned.cil','vendor_sepolicy.cil/android_common/p00a/vendor_sepolicy.cil']
files=[];pins=[]
for idx,rel in enumerate(rels):
 p=root/rel;dest=copies/(str(idx)+'-'+p.name);shutil.copyfile(p,dest);files.append(str(dest));pins.append({'source':str(p),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
cmd=[str(a/'out/host/linux-x86/bin/secilc'),'-m','-M','true','-G','-c','30',*files,'-o',str(out/'policy-checked'),'-f',str(out/'policy-file-contexts')]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
result={'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'inputs':pins,'scope':'Existing SDK37 p00a policy copied to isolated output, neverallow checks enabled (no -N); stage adds zero policy rules; future integrated product must rerun checks'}
(out/'secilc-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
