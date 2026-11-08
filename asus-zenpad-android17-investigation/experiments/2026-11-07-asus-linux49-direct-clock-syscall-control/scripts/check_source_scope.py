"""Bind the complete source to the single declared syscall control delta."""
from pathlib import Path
import difflib,hashlib,json,re
R=Path(__file__).resolve().parents[1]
B=R.parent/'2026-11-07-asus-linux49-runnable-timer-format-fix'
sha=lambda x:hashlib.sha256(x).hexdigest()
old=(B/'source/init.c').read_text();source=(R/'source/init.c').read_text()
assert sha(old.encode())=='d6cf66e19d1f2638941b0f14b0a3428db74b6867bf1761c3491d14188db8e4ad'
id=json.loads((R/'evidence/identity.json').read_text())
expected=old.replace('bee07d4f-f6c2-4845-bfe8-c4745767c216',id['pid1_run_uuid']).replace('ASUS49-RUNNABLE','ASUS49-SYSCLOCK')
expected=expected.replace('#include <sys/sysmacros.h>','#include <sys/sysmacros.h>\n#include <sys/syscall.h>')
expected=expected.replace('static int clock_sample(', 'static int monotonic_clock(struct timespec *t){\n return (int)syscall(SYS_clock_gettime,CLOCK_MONOTONIC,t);\n}\nstatic int clock_sample(')
expected=expected.replace('clock_gettime(CLOCK_MONOTONIC,t)','monotonic_clock(t)').replace('clock_gettime(CLOCK_MONOTONIC,&next)','monotonic_clock(&next)')
expected=expected.replace('static void observe(void){','static void observe(void){\n event("actual","clock.path","CLOCK_MONOTONIC",0,0,"kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed");')
a='  if(!strncmp(p,"GICv2",5)&&(p[5]==\' \'||p[5]==\'\\t\')){chip="GICv2";p+=5;break;}'
expected=expected.replace(a,a+'\n  if(!strncmp(p,"GIC-0",5)&&(p[5]==\' \'||p[5]==\'\\t\')){chip="GIC-0";p+=5;break;}')
assert source==expected,'Undeclared source change'
def fn(s,name):
 m=re.search(r'^(?:static [^\n]+|int) '+name+r'\([^\n]*\)\{',s,re.M);assert m,name
 start=m.start();i=s.index('{',start)+1;depth=1
 while depth:
  if s[i]=='{':depth+=1
  if s[i]=='}':depth-=1
  i+=1
 return s[start:i]+'\n'
normalized=old.replace('bee07d4f-f6c2-4845-bfe8-c4745767c216',id['pid1_run_uuid']).replace('ASUS49-RUNNABLE','ASUS49-SYSCLOCK')
unchanged=['event','begin','end','park','alarm_handler','finish','names','metadata','mmc_snapshot','number','timer_snapshot','main']
for name in unchanged:assert fn(source,name)==fn(normalized,name),name
assert fn(source,'clock_sample')==fn(normalized,'clock_sample').replace('clock_gettime(CLOCK_MONOTONIC,t)','monotonic_clock(t)')
assert source.count('syscall(SYS_clock_gettime,CLOCK_MONOTONIC,t)')==1
assert len(re.findall(r'\bmonotonic_clock\(',source))==3
assert not re.search(r'\bclock_gettime\s*\(',source)
assert source.count('kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed')==1
handler=fn(source,'alarm_handler');assert handler.count('write(')==1 and 'errno=saved' in handler
assert source.count('reboot(RB_AUTOBOOT)')==1 and source.count('alarm(1)')==1
obs=fn(source,'observe');assert 'iterations<2000000' in obs and 'delta>=1500000000LL' in obs
assert not re.search(r'\b(?:sleep|usleep|nanosleep|clock_nanosleep|sched_yield|wait|fork|clone)\s*\(',obs)
rec=dict(source_sha256=sha(source.encode()),base_source_sha256=sha(old.encode()),exact_declared_source_delta=True,all_other_functions_unchanged=True,unchanged_functions=unchanged,clock_calls='initial clock_sample and every observe iteration use monotonic_clock -> syscall(SYS_clock_gettime,CLOCK_MONOTONIC,t)',errno_return_behavior='syscall returns 0 or -1/errno; original caller capture/restoration unchanged',one_clock_path_marker=True,handler_one_write_preserved=True,no_handler_reboot=True,one_normal_reboot=True,interrupt_bounds=dict(bytes=32768,read_calls=8,lines=256,arch_lines=8,cpu_counters=16),loop_bounds=dict(iterations=2000000,counter_delta_ns=1500000000),parser_delta='add exact bounded GIC-0 controller; numeric fields, privacy, optional Level/Edge and read bounds unchanged')
(R/'source/init.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile='runnable-timer-format-fix/source/init.c',tofile='direct-clock-syscall-control/source/init.c')))
with (R/'evidence/source-scope-receipt.json').open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(json.dumps(rec,indent=2))
