"""One explicit source-scope check before the single compiler invocation."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
P=R.parent/'2026-11-07-asus-linux49-ram-before-alarm-probe/source/init.c'
identity=json.loads((R/'evidence/identity.json').read_text())
old=P.read_text()
prior=old.replace('5fa3e2cd-430d-4bbb-8b37-1adff9bb9439',identity['pid1_run_uuid']).replace('ASUS49-PREALARM','ASUS49-RUNNABLE')
source=(R/'source/init.c').read_text()
def fn(s,name):
 m=re.search(r'^(?:static [^\n]+|int) '+name+r'\([^\n]*\)\{',s,re.M);assert m,name
 a=m.start();i=s.index('{',m.start());depth=1;i+=1
 while depth:
  if s[i]=='{':depth+=1
  if s[i]=='}':depth-=1
  i+=1
 return s[a:i]+'\n'
assert source[:source.index('static void event')]==prior[:prior.index('static void event')].replace('static volatile sig_atomic_t sink_error;','static volatile sig_atomic_t sink_error;\nstatic volatile sig_atomic_t alarm_fired;\nstatic const char *phase="setup";')
for n in ['begin','end','park','names','metadata']:assert fn(source,n)==fn(prior,n),n
assert fn(source,'event')==fn(prior,'event').replace('stage=%s op=%s','phase=%s stage=%s op=%s').replace('stage,op,path,rc,error,value','phase,stage,op,path,rc,error,value')
assert fn(source,'clock_sample')==fn(prior,'clock_sample').replace('event("end","clock_gettime",name,rc,e,v);return rc;','event("end","clock_gettime",name,rc,e,v);errno=e;return rc;')
a=prior.index(' names("/sys/class/mmc_host")');z=prior.index(' struct timespec before,after,request=',a)
assert fn(source,'mmc_snapshot')=='static void mmc_snapshot(void){\n int rc;\n'+prior[a:z]+'}\n'
prefix=prior[prior.index('int main(void)'):a]
tail=''' phase="before";mmc_snapshot();
 metadata("/sys/devices/system/clockevents/clockevent0/current_device");
 metadata("/sys/devices/system/clockevents/broadcast/current_device");
 timer_snapshot();
 phase="observe";
 begin("alarm.nominal1s.timer-dependent","-");unsigned left=alarm(1);end("alarm.nominal1s.timer-dependent","-",left,0);
 observe();
 phase="after";timer_snapshot();mmc_snapshot();
 phase="finish";finish();return 0;
}
'''
assert fn(source,'main')==prefix+tail,'Only the declared observation replaces old sleep tail'
names=re.findall(r'^(?:static [^\n]+|int) (\w+)\([^\n]*\)\{',source,re.M)
assert set(names)=={'event','begin','end','park','alarm_handler','finish','clock_sample','names','metadata','mmc_snapshot','number','timer_line','timer_snapshot','observe','main'}
reviewed=json.loads((R/'evidence/reviewed-new-function-pins.json').read_text())
for n,pin in reviewed.items():assert hashlib.sha256(fn(source,n).encode()).hexdigest()==pin,n
handler=fn(source,'alarm_handler')
assert handler.count('write(')==1 and 'alarm_fired=1' in handler
assert not re.search(r'\b(?:reboot|park|event|alarm|printf|snprintf)\s*\(',handler)
obs=fn(source,'observe')
assert 'while(iterations<2000000)' in obs and 'delta>=1500000000LL' in obs
assert obs.count('clock_gettime(CLOCK_MONOTONIC,')==1
loop=obs[obs.index('while(iterations'):obs.index(' }else error=errno;')]
assert not re.search(r'\b(?:event|begin|end|write)\s*\(',loop)
assert not re.search(r'\b(?:sleep|usleep|nanosleep|clock_nanosleep|sched_yield|wait|waitpid|fork|vfork|clone|execve|system)\s*\(',source)
assert source.count('reboot(RB_AUTOBOOT)')==1 and source.count('alarm(1)')==1
snap=fn(source,'timer_snapshot')
assert 'char buf[32769]' in snap and 'calls<8&&used<32768' in snap and 'lines<256' in snap and 'if(found>8)' in snap
assert 'read(fd,buf+used,4096)' in snap
import difflib
(R/'source/init.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile=str(P),tofile=str(R/'source/init.c'))))
receipt=dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),prior_source_sha256=hashlib.sha256(old.encode()).hexdigest(),unchanged_functions=['begin','end','park','names','metadata'],sink_change='phase label only',clock_sample_change='restore captured errno',unchanged_main_setup=True,mmc_body_exact_extraction=True,explicit_main_observation_tail=True,new_functions_pinned=reviewed,interrupt_bounds=dict(bytes=32768,read_calls=8,lines=256,arch_lines=8,cpu_counters=16),loop_bounds=dict(iterations=2000000,counter_delta_ns=1500000000),only_handler_side_effects='sig_atomic_t flag, one nonblocking write, errno preservation',no_handler_reboot=True,one_normal_reboot=True,power_fallback_required=True)
with (R/'evidence/source-scope-receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt,indent=2))
