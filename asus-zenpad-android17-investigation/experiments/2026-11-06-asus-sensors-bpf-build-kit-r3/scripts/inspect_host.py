from pathlib import Path
import json,os,shutil,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
T=Path('/srv/android/lineage24');B=T/'out/host/linux-x86/bin'
rows={'tools':{},'policy':{},'vintf':{},'other_tools':[]}
for name in ['secilc','checkpolicy','checkfc','property_info_checker','host_init_verifier','checkvintf','apexd_host','debugfs']:
 rows['tools'][name]=[str(p) for p in [B/name,Path('/usr/bin')/name,Path('/usr/sbin')/name] if p.is_file()]
for root in [T/'out/target/product/p00a/system',T/'out/soong/.intermediates/system/sepolicy']:
 for p in root.rglob('*'):
  if p.is_file() and (p.name.endswith(('.cil','.conf','_contexts','sepolicy_vers.txt')) or p.name in ['checkfc','checkvintf','property_info_checker']):
   if 'sepolicy' in str(p) or 'selinux' in str(p):rows['policy'][str(p)]=p.stat().st_size
for p in (T/'out/soong/.intermediates').glob('**/linux_glibc_x86_64*/**/checkvintf'):rows['other_tools'].append(str(p))
for p in (T/'out/target/product/p00a/system').glob('*/etc/vintf/*.xml'):rows['vintf'][str(p)]=p.stat().st_size
print(json.dumps(rows))
