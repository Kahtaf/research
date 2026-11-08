exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
script=r'''
from pathlib import Path
import shutil,sys,os,resource,json,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
R=Path('/srv/android/asus-reviewed-build-kit/r8');F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/policy');F.mkdir(parents=True)
sys.path.insert(0,str(R/'scripts'))
from integrate import need,sha,write
from verify_zram_context import verify,lookup
import stat
source=Path('/srv/android/asus-sdk37-lmkd-functional/inputs/fixture-r20/root')
part={k:F/'root'/v for k,v in dict(system='system',vendor='system/vendor',product='system/product',system_ext='system/system_ext').items()}
sourcepins={}
for k,dst in part.items():
 src=source/dst.relative_to(F/'root')/'etc/selinux'
 shutil.copytree(src,dst/'etc/selinux');sourcepins.update({str(p):sha(p) for p in src.rglob('*') if p.is_file()})
version=(part['vendor']/'etc/selinux/plat_sepolicy_vers.txt').read_text().strip()
cil=[part['system']/'etc/selinux/plat_sepolicy.cil',part['system_ext']/'etc/selinux/system_ext_sepolicy.cil',part['product']/'etc/selinux/product_sepolicy.cil',part['vendor']/'etc/selinux/plat_pub_versioned.cil',part['system']/('etc/selinux/mapping/'+version+'.cil'),part['vendor']/'etc/selinux/vendor_sepolicy.cil']
for k in ['system_ext','product']:
 p=part[k]/('etc/selinux/mapping/'+version+'.cil')
 if p.is_file():cil.append(p)
assert all(p.is_file() for p in cil)
tools=Path('/srv/android/lineage24/out/host/linux-x86/bin');policy=F/'policy.bin';args=[str(tools/'secilc'),'-m','-M','true','-G','-c','30',*map(str,cil),'-o',str(policy),'-f',str(F/'generated-contexts')]
r=subprocess.run(args,capture_output=True,text=True);(F/'secilc.log').write_text(r.stdout+r.stderr);assert r.returncode==0
# r20 already carries the exact candidate. Remove only that entry for the
# baseline-selection negative, then append exactly the reviewed source line.
vendor=part['vendor']/'etc/selinux/vendor_file_contexts';old=vendor.read_text();lines=old.splitlines(True);hit=[l for l in lines if l.split()[:1]==['/dev/block/zram0']];assert len(hit)==1 and hit[0].split()==['/dev/block/zram0','u:object_r:swap_block_device:s0']
baseline=''.join(l for l in lines if l not in hit);vendor.write_text(baseline)
combined=F/'baseline-contexts';combined.write_bytes(b'\n'.join((p/('etc/selinux/'+('plat' if k=='system' else k)+'_file_contexts')).read_bytes() for k,p in part.items()))
before=lookup(combined,'/dev/block/zram0',stat.S_IFBLK);assert before=='u:object_r:ram_device:s0'
vendor.write_text(baseline+'/dev/block/zram0    u:object_r:swap_block_device:s0\n')
result=verify(part,policy,tools/'sefcontext_compile',F/'candidate')
# Real context/type validator must reject an unknown target type.
invalid=F/'invalid-context';invalid.write_text('/dev/block/zram0 u:object_r:r8_nonexistent_type:s0\n')
neg=subprocess.run([str(tools/'sefcontext_compile'),'-p',str(policy),'-o',str(F/'invalid.bin'),str(invalid)],capture_output=True,text=True);(F/'invalid.log').write_text(neg.stdout+neg.stderr);assert neg.returncode!=0
result.update(baseline_selected_context=before,cil_sha256={str(p):sha(p) for p in cil},source_policy_inputs=sourcepins,secilc_argv=args,secilc_exit=0,secilc_sha256=sha(tools/'secilc'),neverallow_disabled=False,unknown_type_negative_exit=neg.returncode,one_cpu=True,address_space_bytes=1024**3,actual_post_delta_product_policy=False)
write(F/'result.json',result);print(json.dumps(result,indent=2))
'''
r=m.run(script);Path('2026-11-06-asus-r8-continuation-kit/evidence/policy-fixture.json').write_text(r);d=json.loads(r);print(json.dumps({k:d[k] for k in ['baseline_selected_context','selected_context','policy_sha256','secilc_exit','neverallow_disabled','unknown_type_negative_exit','actual_post_delta_product_policy']},indent=2))
