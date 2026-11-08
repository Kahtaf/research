from pathlib import Path
import gzip,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-sparse-watchdog-observation'
sys.path.insert(0,str(R/'source'));import bootformat as b
save=lambda n,d:(R/'evidence'/n).write_text(json.dumps(d,indent=2)+'\n')
# Compare actual stripped deployment sections with the disassembled unstripped ELF.
def sections(data):
 off=struct.unpack_from('<Q',data,40)[0];size,count,ss=struct.unpack_from('<HHH',data,58)
 rows=[struct.unpack_from('<IIQQQQIIQQ',data,off+j*size) for j in range(count)]
 names=data[rows[ss][4]:rows[ss][4]+rows[ss][5]]
 return {names[row[0]:].split(b'\0',1)[0].decode():data[row[4]:row[4]+row[5]] for row in rows if row[1]!=8}
init=(R/'artifacts/init').read_bytes();un=(R/'artifacts/init.unstripped').read_bytes();a,z=sections(init),sections(un)
for n in ['.text','.rodata']:assert a[n]==z[n]
s=(R/'source/init.c').read_text();base=(R/'source/base/init.c').read_text();i=json.loads((R/'evidence/identity.json').read_text())
# All pre-observe routines, including clock syscall, sink, alarm, timer/MMC and finish unchanged.
restored=s.replace(i['helper_uuid'],'f0c3c82c-d639-4d8a-90f2-155fd4224ceb').replace('#include <sched.h>\n','')
assert restored[:restored.index('static int observe(void)')]==base[:base.index('static void observe(void)')]
assert restored[restored.index('int main(void)'):].replace(' if(observe()){phase="finish";finish();return 0;}',' observe();')==base[base.index('int main(void)'):]
assert s.count('syscall(SYS_sched_setscheduler')==2 and s.count('syscall(SYS_sched_getscheduler')==3 and s.count('syscall(SYS_sched_getparam')==3
assert 'while(iterations<2000000)' in s and 'delta>=1500000000LL' in s
assert s.index('int restore=')<s.index('clock_gettime.final')<s.index('phase="after"')
hd=(R/'evidence/helper-scoped.disasm').read_text()
assert len(re.findall(r'\bbl\s+\w+ <syscall>',hd))==10
for number,count in [('0x71',2),('0x77',2),('0x78',3),('0x79',3)]:
 assert len(re.findall(r'mov\s+x0, #'+number+r'\b',hd))==count,(number,count)
# Exact reviewed machine-code boundaries, bound to deployed .text above.
for fragment in ['400b8c:', 'cbz\tw0, 400bec', '400bfc:', '400d4c:', '400d78:', 'b\t400d68', '400e4c:', 'cbnz\tw0, 400e60', '400e74:', 'b\t400ba8', '400bc8:', 'b\t400784', '400fa8:', 'cbz\tw0, 400bb8']:
 assert fragment in hd,fragment
raw,dt=b.ungzip((R/'artifacts/Image.gz-dtb').read_bytes())
ks=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();kb=(R/'source/base/arch/arm64/kernel/asus_retained_trace.c').read_text()
ops=[('actual',op,'pid0') for op in ['sched.original','sched.boost','sched.boost.observed','sched.restore','sched.restored']]+[('invalid','sched.control','pid0'),('accepted','sched.control','pid0'),('actual','runnable.progress','CLOCK_MONOTONIC')]
added=[' phase=observe stage='+st+' op='+op+' path='+p+' rc=' for st,op,p in ops]
r=ks.replace(i['helper_uuid'],'f0c3c82c-d639-4d8a-90f2-155fd4224ceb')
for prefix in added:
 needle='        PREFIX("'+prefix+'") ||\n';assert r.count(needle)==1;r=r.replace(needle,'')
assert r==kb
# The exact new operation strings survive compilation; prefix comparisons execute
# within linked sparse admission before original writer publication.
for prefix in added:assert prefix.encode()+b'\0' in raw,prefix
assert i['helper_uuid'].encode() in raw and i['mode'].encode() in raw
kd=(R/'evidence/kernel-scoped.disasm').read_text()
assert '<asus_retained_trace_write>:' in kd and 'cmp\tw20, #0x2fe' in kd and 'cmp\tw2, #0x5e' in kd
assert 'b.hi' in kd and 'b.ne' in kd and '<__pi_memcmp>' in kd
obj=(R/'evidence/retained-object.disasm').read_text();nm=(R/'evidence/retained-object.nm').read_text()
assert not re.search(r'\bstlr\b',obj)
for tag in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1','A49DL1']:assert (tag+' uuid=').encode() not in raw
for name in ['cap_init','sw_init','wd_init','ps_init','pm_init','dl_init']:assert not re.search(r'\s'+name+r'(?:\.|$)',nm,re.M)
e=json.loads((R/'evidence/entry-check.json').read_text());ed=e['stext_disasm']
assert 'mov\tx4, #0xf007' in ed and 'movk\tx4, #0x4403, lsl #16' in ed
mapdata=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());mp=json.loads((R/'evidence/System.map-uncompressed.json').read_text())
assert b.sha(mapdata)==mp['sha256']==json.loads((R/'evidence/build-receipt.json').read_text())['artifacts']['System.map']['sha256'] and len(mapdata)==mp['bytes']
package=json.loads((R/'evidence/packaging-receipt.json').read_text())
for n,k in [('candidate.img','candidate'),('candidate.p10.raw','full_p10')]:assert b.sha((R/'artifacts'/n).read_bytes())==package[k]['sha256']
assert json.loads((R/'evidence/plan-isolation-receipt.json').read_text())['actual_installer_main_calls']==1
save('focused-checks.json',dict(status='PASS',deployed_text_and_rodata_match_disassembled_ELF=True,direct_syscalls=dict(clock_gettime=2,sched_setscheduler=2,sched_getscheduler=3,sched_getparam=3),unchanged_preobserve_functions_and_other_main_operations=True,exact_new_sparse_prefixes=added,only_kernel_source_delta='fresh identity and exact helper scheduling/progress prefix additions',sparse_linked_length_ascii_guards_present=True,hot_publish_store_and_header_tags_absent=True,entry_guard_binary='0x4403f007 unchanged',map_exact=True,builds=dict(helper=1,kernel=1),physical_trial=False))
print('PASS focused source, actual binary sections/branches, sparse admissions, entry guard, map and package pins')
