"""Bounded existing-host checks; no Soong/Ninja invocation or active writes."""
import datetime,json,os,re,resource,subprocess
from pathlib import Path
from integrate import sha,write,need
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));os.nice(10)
R=Path(__file__).resolve().parents[1];plan=json.loads((R/'inputs/plan.json').read_text());A=Path(plan['aosp']);P=Path(plan['product_out']);B=A/'out/host/linux-x86/bin';S=Path(plan['staging'])/'product-device/sensors'
O=R/'evidence/bounded-host-r3-v3';O.mkdir(parents=True) # Exclusive evidence, never replace.
rows=[]
def run(args,label):
 args=list(map(str,args));out=O/(label+'.stdout');err=O/(label+'.stderr')
 with out.open('xb') as stdout,err.open('xb') as stderr:
  try:p=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=60);code=p.returncode
  except subprocess.TimeoutExpired:code=124
 row={'argv':args,'exit':code,'stdout':str(out),'stderr':str(err),'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
 if Path(args[0]).is_file():row['tool_sha256']=sha(args[0])
 rows.append(row);write(O/('command-'+str(len(rows))+'.json'),row);return code
for rel in ['init.p00a-accelerometer.rc']:
 run([B/'host_init_verifier',S/rel],'sensor-init')
run([B/'host_init_verifier',A/'hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED'],'genuine-wrapper-init')
# Use installed existing split CIL only as a host baseline, never as r3 outputs.
partitions={'system':P/'system','system_ext':P/'system/system_ext','product':P/'system/product','vendor':P/'system/vendor'}
version=partitions['vendor']/'etc/selinux/plat_sepolicy_vers.txt'
cil=[];missing=[]
if version.is_file():
 v=version.read_text().strip();need(re.fullmatch(r'[0-9.]+',v),'Invalid existing CIL version')
 for label,root in partitions.items():
  name='plat' if label=='system' else label
  path=root/'etc/selinux'/(name+'_sepolicy.cil');cil.append(path)
  mapping=root/'etc/selinux/mapping'/(v+'.cil')
  if mapping.is_file():cil.append(mapping)
 cil.append(partitions['vendor']/'etc/selinux/plat_pub_versioned.cil')
 missing=[str(f) for f in cil if not f.is_file()]
else:
 I=A/'out/soong/.intermediates/system/sepolicy'
 cil=[I/'plat_sepolicy.cil/android_common/plat_sepolicy.cil',I/'system_ext_sepolicy.cil/android_common/p00a/system_ext_sepolicy.cil',I/'product_sepolicy.cil/android_common/p00a/product_sepolicy.cil',I/'vendor_sepolicy.cil/android_common/p00a/vendor_sepolicy.cil',I/'plat_pub_versioned.cil/android_common/p00a/plat_pub_versioned.cil']
 mappings=list((I/'plat_mapping_file/android_common').glob('*.cil'))
 need(len(mappings)==1,'Ambiguous actual policy mapping version')
 cil+=mappings
 for name in ['system_ext','product']:
  f=I/(name+'_mapping_file/android_common/p00a')/mappings[0].name
  if f.is_file():cil.append(f)
 missing=[str(f) for f in cil if not f.is_file()]
# Translate only this macro-free pinned TE subset into an additional CIL module.
# This cannot substitute for Soong's final sepolicy build and context generation.
fragment=[]
for line in (S/'sepolicy/p00a_accelerometer.te').read_text().splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.fullmatch(r'type (\w+), (.+);',line)
 if m:
  name,attrs=m.groups();fragment.append('(type '+name+')');fragment.append('(roletype object_r '+name+')')
  fragment.extend('(typeattributeset '+attr.strip()+' ('+name+'))' for attr in attrs.split(','));continue
 m=re.fullmatch(r'allow (\w+) (\w+):(\w+) (?:\{ )?([\w ]+?)(?: \})?;',line)
 need(m is not None,'Unsupported actual sensor TE statement: '+line)
 source,target,cls,perms=m.groups();fragment.append(f'(allow {source} {target} ({cls} ({perms})))')
for line in (S/'sepolicy/genfs_contexts').read_text().splitlines():
 if not line.strip() or line.startswith('#'):continue
 fs,path,context=line.split()[1:];user,role,type_,level=context.split(':')
 fragment.append(f'(genfscon {fs} {path} ({user} {role} {type_} (({level}) ({level}))))')
extra=O/'sensor-translated.cil';extra.write_text('\n'.join(fragment)+'\n')
base_status=candidate_status=negative_status=None
if not missing:
 cmd=[B/'secilc','-m','-M','true','-G','-c','30',*cil]
 base_status=run(cmd+['-o',O/'baseline.policy','-f',O/'baseline.contexts'],'baseline-cil-neverallows')
 candidate_status=run(cmd+[extra,'-o',O/'candidate.policy','-f',O/'candidate.contexts'],'candidate-cil-neverallows')
 denial=O/'deliberate-neverallow.cil';denial.write_text('(neverallow hal_sensors_default p00a_accel_device (chr_file (open)))\n')
 negative_status=run(cmd+[extra,denial,'-o',O/'negative.policy','-f',O/'negative.contexts'],'negative-neverallow')
tools={name:B/name for name in ['checkfc','property_info_checker','checkvintf']}
for name,rel in {'checkfc':'system/sepolicy/tools/checkfc/linux_glibc_x86_64/checkfc','property_info_checker':'system/core/property_service/property_info_checker/linux_glibc_x86_64/property_info_checker','checkvintf':'system/libvintf/checkvintf/linux_glibc_x86_64/checkvintf'}.items():
 candidate=A/'out/soong/.intermediates'/rel
 if not tools[name].is_file() and candidate.is_file():tools[name]=candidate
if candidate_status==0:
 if tools['checkfc'].is_file():run([tools['checkfc'],O/'candidate.policy',S/'sepolicy/file_contexts'],'sensor-file-contexts')
 if tools['property_info_checker'].is_file():
  contexts=[root/'etc/selinux'/(('plat' if name=='system' else name)+'_property_contexts') for name,root in partitions.items()]
  run([tools['property_info_checker'],O/'candidate.policy',*contexts],'existing-property-contexts')
# Existing framework matrices/installed manifests do not contain the r3 product;
# run actual checkvintf only with an isolated overlay if that tool already exists.
vintf_status='not-run: actual checkvintf is absent; r6 build must produce it'
if tools['checkvintf'].is_file():
 import shutil,xml.etree.ElementTree as ET
 vendor=O/'vendor';(vendor/'etc').mkdir(parents=True)
 shutil.copytree(partitions['vendor']/'etc/vintf',vendor/'etc/vintf')
 manifest=vendor/'etc/vintf/manifest.xml';tree=ET.parse(manifest);addition=ET.parse(S/'manifest.xml')
 for hal in addition.getroot():tree.getroot().append(hal)
 tree.write(manifest)
 cmd=[tools['checkvintf'],'--check-compat','--dirmap','/vendor:'+str(vendor)]
 for name in ['system','system_ext','product']:cmd+=['--dirmap','/'+name+':'+str(partitions[name])]
 cmd+=['--kernel',plan['kernel_release']+':'+plan['config'],'--property','ro.product.first_api_level=23']
 vintf_status=run(cmd,'candidate-vintf-overlay')
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':rows,'existing_cil_inputs':{str(p):sha(p) for p in cil if p.is_file()},'missing_cil':missing,'candidate_te_sha256':sha(S/'sepolicy/p00a_accelerometer.te'),'candidate_genfs_sha256':sha(S/'sepolicy/genfs_contexts'),'baseline_cil_exit':base_status,'candidate_translated_cil_exit':candidate_status,'deliberate_neverallow_exit':negative_status,'missing_native_tools':[k for k,v in tools.items() if not v.is_file()],'vintf_status':vintf_status,'actual_r3_soong_policy_verified':False,'active_written':False,'product_build_started':False,'flash_ready':False,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
write(O/'result.json',summary);print(json.dumps(summary,indent=2))
