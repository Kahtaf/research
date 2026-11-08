"""One focused offline proof; no helper/kernel compilation or device contact."""
from pathlib import Path
import ctypes, hashlib, json, re, shutil, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-normal-ram-compute-control'
E=R/'evidence';A=R/'artifacts'
sys.path.insert(0,str(R/'source'));import bootformat as b
sys.path.insert(0,str(R/'scripts'));import decode_compute as d
I=d.I
sha=lambda x:hashlib.sha256(x).hexdigest()
save=lambda n,x:(E/n).write_text(json.dumps(x,indent=2)+'\n')
def boundary(event,args):
    if event=='open':
        p=str(args[0]);assert not any(s in p for s in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/')),p
    if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)

# Exact source subtraction and unchanged baseline inputs, checked before and after.
pre=json.loads((E/'base-source-pre.json').read_text())
post={n:sha((B/n).read_bytes()) for n in pre};assert post==pre
save('base-source-post.json',post)
s=(R/'source/init.c').read_text();old=(B/'source/init.c').read_text()
remove='''  if(iterations==500000||iterations==1000000||iterations==1500000){
   char progress[96];snprintf(progress,sizeof(progress),"iterations=%u checksum=%08x",(unsigned)iterations,(unsigned)checksum);
   event("actual","runnable.progress","CLOCK_MONOTONIC",0,0,progress);
  }
'''
assert old.count(remove)==1
assert s==old.replace(remove,'').replace('03f2153c-4faf-41ba-9f66-bcd8d4b1aa9f',I['control_uuid']).replace(';loop=pure-compute-normal"',';loop=pure-compute-normal-final-only"')
assert not any(x in s for x in ['runnable.progress','SYS_sched_setscheduler','SCHED_FIFO','SCHED_RR','clock_gettime.final'])
assert s[s.index('int main(void)'):]==old[old.index('int main(void)'):]

def sections(data):
    off=struct.unpack_from('<Q',data,40)[0];size,count,ss=struct.unpack_from('<HHH',data,58)
    rows=[struct.unpack_from('<IIQQQQIIQQ',data,off+j*size) for j in range(count)]
    names=data[rows[ss][4]:rows[ss][4]+rows[ss][5]]
    return {names[r[0]:].split(b'\0',1)[0].decode():(r[3],data[r[4]:r[4]+r[5]]) for r in rows if r[1]!=8}
init=(A/'init').read_bytes();un=(A/'init.unstripped').read_bytes();ds,us=sections(init),sections(un)
for n in ['.text','.rodata']:assert ds[n]==us[n]
hd=(E/'helper-scoped.disasm').read_text();textbase,textbytes=ds['.text'];words=0
for address,code in re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s',hd,re.M):
    off=int(address,16)-textbase;assert textbytes[off:off+4]==int(code,16).to_bytes(4,'little');words+=1
def fn(name):return hd.split('<'+name+'>:\n',1)[1].split('\nDisassembly of section',1)[0]
compute=fn('compute_loop');observe=fn('observe');main=fn('main')
assert b'runnable.progress' not in init
assert set(re.findall(r'\bbl\s+\w+ <([^>]+)>',compute))=={'___snprintf_chk','event','__stack_chk_fail'}
assert len(re.findall(r'\bbl\s+\w+ <event>',compute))==1
instructions={int(a,16):asm.strip().split('//')[0].strip() for a,asm in re.findall(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+(.+)$',compute,re.M)}
body=[instructions[a] for a in range(0x400e98,0x400eb4,4)]
assert body==['ldr\tw0, [sp, #4]','add\tw5, w5, #0x1','madd\tw0, w0, w3, w2','eor\tw0, w0, w5','str\tw0, [sp, #4]','cmp\tw5, w1','b.ne\t400e98 <compute_loop+0x4c>']
assert not re.search(r'\b(?:bl|blr|svc)\b','\n'.join(body))
def immediate(addr):return int(re.search(r'#(0x[0-9a-f]+)',instructions[addr])[1],16)
mult=immediate(0x400e50)|(immediate(0x400e6c)<<16)
add=immediate(0x400e5c)|(immediate(0x400e74)<<16)
seed=immediate(0x400e84)|(immediate(0x400e8c)<<16)
cap=immediate(0x400e88)|(immediate(0x400e90)<<16)
assert (mult,add,seed,cap)==(1664525,1013904223,0x6d2b79f5,2000000)
x=seed
for n in range(1,cap+1):x=((x*mult+add)&0xffffffff)^n
assert f'{x:08x}'==d.CHECKSUM=='e4ca7075'
assert compute.index('400eb0:')<compute.index('<___snprintf_chk>')<compute.index('<event>')
assert len(re.findall(r'\bbl\s+\w+ <syscall>',observe))==3
for number in ['0x71','0x78','0x79']:assert len(re.findall(r'mov\s+x0, #'+number+r'\b',observe))==1
for fragment in ['orr\tw19, w19, w21','orr\tw19, w19, w20','cbz\tw19, 402004','bl\t400e4c <compute_loop>']:assert fragment in observe
assert main.index('<observe>')<main.rindex('<timer_snapshot>')<main.rindex('<mmc_snapshot>')

# Run the previously compiled predicate verifier; no new native/helper/kernel build.
ks=(R/'source/reused/asus_retained_trace.c').read_text()
pred=ks[ks.index('static bool sparse_prefix('):ks.index('/* Keep the first text;')]
verifier='#include <stdbool.h>\n#include <string.h>\n#include "../source/reused/asus_entry_tag.h"\n'+pred+'\nbool check(const char *s,unsigned int n){return sparse_admit(s,n);}\n'
assert verifier==(B/'evidence/sparse-filter-verifier.c').read_text()
for n in ['sparse-filter-verifier.c','sparse-filter-verifier.dylib']:shutil.copy2(B/'evidence'/n,E/n)
lib=ctypes.CDLL(str(E/'sparse-filter-verifier.dylib'));lib.check.argtypes=[ctypes.c_char_p,ctypes.c_uint];lib.check.restype=ctypes.c_bool
admit=lambda line:bool(lib.check(line.encode(),len(line.encode())))
def event(phase,stage,op,path,rc=0,err=0,value='-'):
    return I['helper_prefix']+f' phase={phase} stage={stage} op={op} path={path} rc={rc} errno={err} value={value}'
fresh=event('observe','actual','clock.path','CLOCK_MONOTONIC',value=d.CLOCK_PATH)
complete=event('observe','complete','runnable.loop','CLOCK_MONOTONIC',value='control='+I['control_uuid']+' iterations=2000000 checksum='+d.CHECKSUM+' reason=compute-cap')
assert admit(fresh) and admit(complete) and admit(fresh.replace(I['control_uuid'],'00000000-0000-0000-0000-000000000000')) and not admit(I['helper_prefix'])
raw,dt=b.ungzip((A/'Image.gz-dtb').read_bytes())
for stage,op,path in [('actual','clock.path','CLOCK_MONOTONIC'),('complete','runnable.loop','CLOCK_MONOTONIC'),('actual','sched.original','pid0')]:
    assert (' phase=observe stage='+stage+' op='+op+' path='+path+' rc=').encode()+b'\0' in raw
kd=(E/'reused-kernel-scoped.disasm').read_text()
for fragment in ['<asus_retained_trace_write>:','cmp\tw20, #0x2fe','cmp\tw2, #0x5e','<__pi_memcmp>','mov\tx4, #0xf007','movk\tx4, #0x4403, lsl #16']:assert fragment in kd
assert I['control_uuid'].encode() not in raw

def irq(phase,count):
    return [event(phase,'actual','interrupts.arch_timer','/proc/interrupts',value=f'irq=30 counts={count} cpus=1 controller=GICv2 hwirq=30 trigger=Level name=arch_timer'),
            event(phase,'complete','interrupts.snapshot','/proc/interrupts',1,value='bytes=100 read_calls=2 lines=1 arch_found=1 emitted=1 parse_or_read_errors=0 eof=1')]
lines=['ASUS49-ENTRY run='+I['kernel_uuid']+' stage=stext-preargs release='+d.RELEASE,I['mode'],
       event('setup','actual','getpid','-',1,value='PID1-required'),event('setup','actual','uname.release','-',value=d.RELEASE),*irq('before',10),
       event('observe','begin','alarm.nominal1s.timer-dependent','-'),event('observe','end','alarm.nominal1s.timer-dependent','-'),fresh,
       event('observe','begin','clock_gettime','loop.initial'),event('observe','end','clock_gettime','loop.initial',value='1.000000000'),
       event('observe','actual','sched.original','pid0',value='getparam_rc=0 getparam_errno=0 priority=0')]
partial='\n'.join(lines+[complete]);good='\n'.join(lines+[complete]+irq('after',11))
full=d.P['full_p10']['sha256'];bound=lambda t:d.decode(t,full,'SYNTHETIC-NEW-BOOT','SYNTHETIC-COMPLETE-CONSOLE')
controls=dict(complete_after_irq=good,partial_2m=partial,missing_2m='\n'.join(lines),
    stale_control=good.replace(I['control_uuid'],'03f2153c-4faf-41ba-9f66-bcd8d4b1aa9f'),
    prefix_only=good.replace(d.CLOCK_PATH,'kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed'),
    prior_progress=partial+'\n'+event('observe','actual','runnable.progress','CLOCK_MONOTONIC',value='iterations=500000 checksum=bf1c9915'),
    wrong_checksum=good.replace('checksum=e4ca7075','checksum=00000000'),
    policy_refused='\n'.join(lines[:-1]+[event('observe','actual','sched.original','pid0',1,value='getparam_rc=0 getparam_errno=0 priority=1'),event('observe','invalid','sched.control','pid0',-1,value='baseline-refused;require-SCHED_OTHER-priority0;no-schedule-mutation')]))
results={n:bound(t) for n,t in controls.items()}
assert results['complete_after_irq']['status']=='COMPUTE_AND_AFTER_IRQ_PUBLISHED'
assert results['complete_after_irq']['completion_write_return']=='PROVEN_BY_SAME_THREAD_AFTER_IRQ'
assert results['complete_after_irq']['timer_observations']['irq_growth']=='GROWTH_OBSERVED'
assert results['partial_2m']['compute_cap_published'] and results['partial_2m']['complete_after_irq']=='UNKNOWN'
assert results['missing_2m']['status']=='UNKNOWN_STOP' and results['missing_2m']['normal_policy_verified']
for n in ['stale_control','prefix_only','prior_progress','wrong_checksum','policy_refused']:assert not results[n]['control_accepted'] and not results[n]['compute_cap_published']
assert results['policy_refused']['status']=='CONTROL_INVALID'
unbound=d.decode(good);wrongfull=d.decode(good,'0'*64,'SYNTHETIC','SYNTHETIC')
assert not unbound['control_accepted'] and not wrongfull['control_accepted']
assert not d.decode(good,full,'SYNTHETIC-NEW-BOOT')['control_accepted']
save('decoder-controls.json',dict(synthetic_only=True,device_boots=0,results=results,unbound=unbound,wrong_full_p10=wrongfull))
plan=json.loads((E/'plan-isolation-receipt.json').read_text());assert plan['actual_installer_main_calls']==1 and not plan['device_contacted']
compile=json.loads((E/'compiler-receipt.json').read_text());assert compile['helper_compiles']==1 and compile['kernel_builds']==0
package=json.loads((E/'packaging-receipt.json').read_text());assert all(v is True for k,v in package['preservation'].items() if isinstance(v,bool))
assert package['initrd']['unchanged_entry_guard_end']=='0x4403f007' and package['initrd']['remaining_guard_bytes']>0
save('focused-checks.json',dict(status='PASS',helper_compiles=1,kernel_builds=0,source_delta_exact=True,baseline_source_pre_post_unchanged=True,
    deployed_text_rodata_equal_unstripped=True,instruction_words_bound_to_delivered_binary=words,
    compute_backedge='0x400e98..0x400eb0; volatile ldr/add/madd/eor/str/cmp/b.ne; no calls',
    compute_event_calls=1,completion_event_address='0x400efc',intermediate_milestone_calls=0,
    binary_constants=dict(seed=hex(seed),multiplier=mult,increment=add,iterations=cap),calculated_checksum=f'{x:08x}',
    checksum_limit='Independent recurrence evaluation from disassembled constants, not a device/emulator execution.',
    direct_syscalls=dict(clock_gettime=1,sched_getscheduler=1,sched_getparam=1,sched_setscheduler=0,inside_compute_backedge=0),
    normal_policy_zero_gate='0x401f98..0x401fa4; compute call 0x402004; refusal finishes unchanged',
    sparse=dict(predicate_sha256=sha(pred.encode()),reused_native_verifier_sha256=sha((E/'sparse-filter-verifier.dylib').read_bytes()),new_native_compiles=0,fresh_values_admitted=True,stale_values_also_admitted=True,kernel_linked_disassembly_bound=True),
    parser_controls='8 synthetic transcripts plus missing binding, console attestation and wrong-p10 checks; no device data',
    isolated_plan_calls=1,no_private_device_subprocess_or_network_inputs=True))
print('PASS: exact source subtraction, actual binary loop/checksum, reused kernel/filter/guard/layout, focused parser controls and one PLAN')
