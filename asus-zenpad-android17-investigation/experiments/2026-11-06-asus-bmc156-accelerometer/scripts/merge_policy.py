from pathlib import Path
import subprocess,json,hashlib,shutil,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1');A=Path('/srv/android/lineage24');B=A/'out/host/linux-x86/bin';O=R/'policy-merge';O.mkdir(exist_ok=True);F=O/'frozen'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
if not F.exists():shutil.copytree('/srv/android/asus-build-continuation/policy-merge-r3/frozen',F)
records=[]
def run(args):
 cmd=list(map(str,args));p=subprocess.run(cmd,capture_output=True,text=True)
 records.append(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/policy-merge.json').write_text(json.dumps(records,indent=2)+'\n');print(p.returncode,p.stdout,p.stderr);assert p.returncode==0
mask=F/'reqd_policy_mask.cil/android_common/reqd_policy_mask.cil';pub=F/'pub_policy.cil/android_common/p00a/pub_policy.cil';plat=F/'plat_sepolicy.cil/android_common/plat_sepolicy.cil';ext=F/'system_ext_sepolicy.cil/android_common/p00a/system_ext_sepolicy.cil';product=F/'product_sepolicy.cil/android_common/p00a/product_sepolicy.cil';pubversion=F/'plat_pub_versioned.cil/android_common/p00a/plat_pub_versioned.cil';mapping=F/'plat_mapping_file/android_common/202704.cil'
raw=O/'vendor.unversioned.cil';shutil.copyfile(R/'policy/policy.cil',raw)
run([B/'build_sepolicy','filter_out','-f',mask,'-t',raw])
vm=O/'vendor.mapping.cil';at=O/'vendor.attributized.cil';vendor=O/'vendor.cil'
run([B/'version_policy','-b',pub,'-n','202704','-o',vm,'-m'])
run([B/'version_policy','-b',pub,'-n','202704','-t',raw,'-o',at])
run([B/'build_sepolicy','filter_out','-f',vm,'-t',at]);vendor.write_bytes(vm.read_bytes()+at.read_bytes())
run([B/'build_sepolicy','filter_out','-f',pubversion,'-t',vendor])
run([B/'secilc','-m','-M','true','-G','-c','30',plat,ext,product,pubversion,mapping,vendor,'-o',O/'policy.bin','-f',O/'generated-file-contexts'])
checkfc=Path('/srv/android/asus-build-continuation/policy-tools-r1/checkfc')
run([checkfc,O/'policy.bin',R/'source/hal/sepolicy/file_contexts'])
run([B/'host_init_verifier',R/'source/hal/init.p00a-accelerometer.rc'])
print('Frozen SDK37 merged policy passed WITH neverallow checks; no active integration.')
