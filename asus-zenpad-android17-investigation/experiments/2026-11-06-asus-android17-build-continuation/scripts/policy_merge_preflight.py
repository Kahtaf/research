#!/usr/bin/env python3
import pathlib,hashlib,subprocess,json,sys,shutil
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');B=A/'out/host/linux-x86/bin';I=A/'out/soong/.intermediates/system/sepolicy';O=R/('policy-merge-'+sys.argv[1]);O.mkdir();records=[];pins={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen(relative):
 p=I/relative;q=O/'frozen'/relative;q.parent.mkdir(parents=True,exist_ok=True);before=sha(p);shutil.copyfile(p,q);assert before==sha(p)==sha(q);pins[str(p)]={'sha256':before,'mtime_ns':p.stat().st_mtime_ns};return q
mask=frozen('reqd_policy_mask.cil/android_common/reqd_policy_mask.cil');pub=frozen('pub_policy.cil/android_common/p00a/pub_policy.cil');plat=frozen('plat_sepolicy.cil/android_common/plat_sepolicy.cil');ext=frozen('system_ext_sepolicy.cil/android_common/p00a/system_ext_sepolicy.cil');product=frozen('product_sepolicy.cil/android_common/p00a/product_sepolicy.cil');pubversion=frozen('plat_pub_versioned.cil/android_common/p00a/plat_pub_versioned.cil');mapping=frozen('plat_mapping_file/android_common/202704.cil')
def run(args):
 p=subprocess.run([str(a) for a in args],capture_output=True);records.append({'argv':[str(a) for a in args],'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()});(O/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 if p.returncode:print(p.stderr.decode()[-12000:]);raise SystemExit(p.returncode)
raw=O/'vendor.unversioned.cil';shutil.copyfile(R/('policy-'+sys.argv[2])/'policy.cil',raw)
run([B/'build_sepolicy','filter_out','-f',mask,'-t',raw])
vm=O/'vendor.mapping.cil';at=O/'vendor.attributized.cil';vendor=O/'vendor.cil'
run([B/'version_policy','-b',pub,'-n','202704','-o',vm,'-m'])
run([B/'version_policy','-b',pub,'-n','202704','-t',raw,'-o',at])
run([B/'build_sepolicy','filter_out','-f',vm,'-t',at]);vendor.write_bytes(vm.read_bytes()+at.read_bytes())
run([B/'build_sepolicy','filter_out','-f',pubversion,'-t',vendor])
run([B/'secilc','-m','-M','true','-G','-c','30',plat,ext,product,pubversion,mapping,vendor,'-o',O/'policy.bin','-f',O/'generated-file-contexts'])
run([B/'checkfc',O/'policy.bin',R/'product-device/radio/sepolicy/file_contexts'])
contexts=[]
for partition,path in [('plat','android_common'),('system_ext','android_common/p00a'),('product','android_common/p00a'),('vendor','android_common/p00a')]:contexts.append(frozen(f'contexts/{partition}_property_contexts/{path}/{partition}_property_contexts'))
run([B/'property_info_checker',O/'policy.bin',*contexts,R/'product-device/radio/sepolicy/property_contexts'])
(O/'evidence.json').write_text(json.dumps({'platform_inputs':pins,'merged_policy_sha256':sha(O/'policy.bin'),'neverallow_enforced':True,'preflight_only_final_soong_pending':True},indent=2)+'\n');print('Merged policy and radio contexts PASS, neverallow checks enabled')
