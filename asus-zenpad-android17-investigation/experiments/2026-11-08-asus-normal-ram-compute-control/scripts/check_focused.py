"""Focused binary/preservation proof plus tiny exact-filter and decoder controls."""
from pathlib import Path
import ctypes,hashlib,json,re,shutil,struct,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-pid1-fifo-loop-control'
sys.path.insert(0,str(R/'source'));import bootformat as b
sys.path.insert(0,str(R/'scripts'));import decode_compute as d
I=d.I;E=R/'evidence';A=R/'artifacts'
sha=lambda x:hashlib.sha256(x).hexdigest()
save=lambda n,x:(E/n).write_text(json.dumps(x,indent=2)+'\n')

def boundary(event,args):
    if event=='open':
        p=str(args[0]);assert not any(s in p for s in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/')),p
    if event.startswith('socket.') or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
    if event=='subprocess.Popen':assert args[0]=='/usr/bin/clang','Only isolated native filter verifier compilation allowed'
sys.addaudithook(boundary)

s=(R/'source/init.c').read_text();old=(B/'source/init.c').read_text()
normalized=s.replace('#include <stdint.h>\n','').replace('#define CONTROL_ID "'+I['control_uuid']+'"\n','')
assert normalized[:normalized.index('/* Volatile uint32_t')]==old[:old.index('static int observe(void)')]
assert s[s.index('int main(void)'):]==old[old.index('int main(void)'):]
assert not any(x in s for x in ['SYS_sched_setscheduler','SCHED_FIFO','SCHED_RR','clock_gettime.final','delta_ns='])
assert s.count('syscall(SYS_sched_getscheduler,')==s.count('syscall(SYS_sched_getparam,')==1
assert 'volatile uint32_t checksum' in s and 'while(iterations<UINT32_C(2000000))' in s

# Every instruction shown is bound to the delivered, stripped executable text.
def sections(data):
    off=struct.unpack_from('<Q',data,40)[0];size,count,ss=struct.unpack_from('<HHH',data,58)
    rows=[struct.unpack_from('<IIQQQQIIQQ',data,off+j*size) for j in range(count)]
    names=data[rows[ss][4]:rows[ss][4]+rows[ss][5]]
    return {names[r[0]:].split(b'\0',1)[0].decode():(r[3],data[r[4]:r[4]+r[5]]) for r in rows if r[1]!=8}
init=(A/'init').read_bytes();un=(A/'init.unstripped').read_bytes();ds,us=sections(init),sections(un)
for n in ['.text','.rodata']:assert ds[n]==us[n]
hd=(E/'helper-scoped.disasm').read_text()
textbase,textbytes=ds['.text']
for address,code in re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s',hd,re.M):
    off=int(address,16)-textbase;assert textbytes[off:off+4]==int(code,16).to_bytes(4,'little')
def fn(name):return hd.split('<'+name+'>:\n',1)[1].split('\nDisassembly of section',1)[0]
compute=fn('compute_loop');observe=fn('observe');main=fn('main')
assert not re.search(r'\b(?:svc|blr)\b|<syscall>|<.*(?:clock|sleep|sched|read|pause).*?>',compute)
assert set(re.findall(r'\bbl\s+\w+ <([^>]+)>',compute))=={'___snprintf_chk','event','__stack_chk_fail'}
for fragment in ['ldr\tw0, [sp, #4]','madd\tw0, w0, w21, w22','eor\tw0, w0, w19','str\tw0, [sp, #4]',
                 'mov\tw0, #0x8480','movk\tw0, #0x1e, lsl #16','cmp\tw19, w0','b.ne\t400eb4']:
    assert fragment in compute,fragment
assert len(re.findall(r'\bbl\s+\w+ <syscall>',observe))==3
for number in ['0x71','0x78','0x79']:assert len(re.findall(r'mov\s+x0, #'+number+r'\b',observe))==1
for fragment in ['orr\tw19, w19, w21','orr\tw19, w19, w20','cbz\tw19, 4020a0','bl\t400e4c <compute_loop>']:
    assert fragment in observe,fragment
assert main.index('<observe>')<main.rindex('<timer_snapshot>')<main.rindex('<mmc_snapshot>')
# Completion is compute_loop's second and last event; source and binary correspond.
assert len(re.findall(r'\bbl\s+\w+ <event>',compute))==2
assert s.index('event("complete","runnable.loop"')<s.index('phase="after"')

# Actual sparse C predicates are extracted byte-for-byte, with unchanged header.
# This tiny host verifier is not a helper or kernel build, nor ARM kernel execution.
reuse=R/'source/reused';reuse.mkdir(exist_ok=True)
for n in ['asus_retained_trace.c','asus_entry_tag.h']:shutil.copy2(B/'source/arch/arm64/kernel'/n,reuse/n)
ks=(reuse/'asus_retained_trace.c').read_text();pred=ks[ks.index('static bool sparse_prefix('):ks.index('/* Keep the first text;')]
verifier='#include <stdbool.h>\n#include <string.h>\n#include "../source/reused/asus_entry_tag.h"\n'+pred+'\nbool check(const char *s,unsigned int n){return sparse_admit(s,n);}\n'
(E/'sparse-filter-verifier.c').write_text(verifier)
command=['/usr/bin/clang','-dynamiclib','-Os','-o',str(E/'sparse-filter-verifier.dylib'),str(E/'sparse-filter-verifier.c')]
p=subprocess.run(command,capture_output=True,text=True);(E/'sparse-filter-compile.log').write_text(p.stdout+p.stderr);p.check_returncode()
lib=ctypes.CDLL(str(E/'sparse-filter-verifier.dylib'));lib.check.argtypes=[ctypes.c_char_p,ctypes.c_uint];lib.check.restype=ctypes.c_bool
admit=lambda line:bool(lib.check(line.encode(),len(line.encode())))
def event(phase,stage,op,path,rc=0,err=0,value='-'):
    return I['helper_prefix']+f' phase={phase} stage={stage} op={op} path={path} rc={rc} errno={err} value={value}'
fresh=event('observe','actual','clock.path','CLOCK_MONOTONIC',value=d.CLOCK_PATH)
complete=event('observe','complete','runnable.loop','CLOCK_MONOTONIC',value='control='+I['control_uuid']+' iterations=2000000 checksum='+d.CHECKSUMS[2000000]+' reason=compute-cap')
assert admit(fresh) and admit(complete)
assert admit(fresh.replace(I['control_uuid'],'00000000-0000-0000-0000-000000000000'))
assert not admit(I['helper_prefix'])
# The exact reused Image also contains the unchanged prefix predicates; linked
# writer disassembly confirms size/ASCII/compare gating before publication.
compiled=(A/'Image.gz-dtb').read_bytes();raw,dt=b.ungzip(compiled)
assert compiled==(B/'artifacts/Image.gz-dtb').read_bytes()
for st,op,path in [('actual','clock.path','CLOCK_MONOTONIC'),('actual','runnable.progress','CLOCK_MONOTONIC'),('complete','runnable.loop','CLOCK_MONOTONIC'),('actual','sched.original','pid0')]:
    assert (' phase=observe stage='+st+' op='+op+' path='+path+' rc=').encode()+b'\0' in raw
kd=(E/'reused-kernel-scoped.disasm').read_text()
for fragment in ['<asus_retained_trace_write>:','cmp\tw20, #0x2fe','cmp\tw2, #0x5e','<__pi_memcmp>','mov\tx4, #0xf007','movk\tx4, #0x4403, lsl #16']:assert fragment in kd,fragment
assert I['control_uuid'].encode() not in raw
# Reconstructed baseline cpio is exact, so no hidden non-init metadata changed.
_,k,ram,_=b.parse_image((B/'artifacts/candidate.img').read_bytes());cp,tail=b.ungzip(ram[512:]);entries=b.parse_cpio(cp)
assert not tail and b.make_cpio(entries)==cp
newcp,tail=b.ungzip((A/'initramfs.cpio.gz').read_bytes());newentries=b.parse_cpio(newcp)
assert not tail and {n:v for n,v in entries.items() if n!='init'}=={n:v for n,v in newentries.items() if n!='init'}
assert entries['init'][:3]==newentries['init'][:3] and newentries['init'][3]==init
assert (A/'initramfs.cpio.gz').read_bytes()[:10]==ram[512:522]

# Five small decoder controls target freshness, bounded arithmetic and missing output.
lines=['ASUS49-ENTRY run='+I['kernel_uuid']+' stage=stext-preargs release='+d.RELEASE,I['mode'],
       event('setup','actual','getpid','-',1,value='PID1-required'),event('setup','actual','uname.release','-',value=d.RELEASE),
       event('observe','begin','alarm.nominal1s.timer-dependent','-'),event('observe','end','alarm.nominal1s.timer-dependent','-'),fresh,
       event('observe','begin','clock_gettime','loop.initial'),event('observe','end','clock_gettime','loop.initial',value='1.000000000'),
       event('observe','actual','sched.original','pid0',value='getparam_rc=0 getparam_errno=0 priority=0')]
for n in [500000,1000000,1500000]:lines.append(event('observe','actual','runnable.progress','CLOCK_MONOTONIC',value=f'iterations={n} checksum={d.CHECKSUMS[n]}'))
lines.append(complete);good='\n'.join(lines)
full=d.P['full_p10']['sha256']
controls={
    'exact_control':good,
    'stale_uuid':good.replace(I['control_uuid'],'00000000-0000-0000-0000-000000000000'),
    'prefix_without_fresh_value':good.replace(d.CLOCK_PATH,'kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed'),
    'missing_completion':'\n'.join(lines[:-1]),
    'wrong_checksum':good.replace('checksum='+d.CHECKSUMS[2000000],'checksum=00000000'),
}
results={n:d.decode(t,full,'SYNTHETIC-NO-PHYSICAL-BOOT') for n,t in controls.items()}
assert results['exact_control']['control_accepted'] and results['exact_control']['compute_cap_published']
assert all(not v['control_accepted'] for n,v in results.items() if n!='exact_control')
assert len(results['missing_completion']['conditional_progress'])==3 and results['missing_completion']['status']=='UNKNOWN_STOP'
assert not d.decode(good)['control_accepted']
save('decoder-controls.json',dict(synthetic_only=True,actual_device_boots=0,results=results,without_physical_binding=d.decode(good)))
plan=json.loads((E/'plan-isolation-receipt.json').read_text());assert plan['actual_installer_main_calls']==1 and not plan['device_contacted']
vm=json.loads((E/'after.stdout').read_text());assert vm['status']=='TERMINATED' and vm['id']=='8549823276971553556'
assert not Path('/tmp/ascomp-'+I['control_uuid'][:8]).exists()
save('focused-checks.json',dict(status='PASS',helper_compiles=1,kernel_builds=0,deployed_text_rodata_and_disassembly_bytes_bound=True,
    arithmetic='uint32 volatile load/madd/eor/store survives on backedge at 0x400eb4; cap 0x1e8480',
    direct_syscalls=dict(clock_gettime=1,sched_getscheduler=1,sched_getparam=1,sched_setscheduler=0,inside_compute_loop=0),
    original_setup_sink_proc_sysfs_MMC_beforeIRQ_alarm_initial_clock_and_finish_preserved=True,
    checksum_milestones=d.CHECKSUMS,unchanged_sparse_predicate_source_sha256=sha(pred.encode()),
    sparse_verification='Unchanged source predicates executed in one tiny native verifier; exact kernel image and matching linked admission disassembly separately bound. No ARM kernel runtime execution.',
    sparse_fresh_value_admitted=True,sparse_values_are_not_identity_guards=True,decoder_stale_prefix_only_missing_completion_wrong_checksum_controls=True,
    cpio_except_init_and_gzip_header_preserved=True,plan_main_calls=1,vm_id=vm['id'],vm_status=vm['status'],owned_master_closed=True))
print('PASS: focused binary, preservation, sparse admission and five synthetic decoder controls; one PLAN; VM TERMINATED')
