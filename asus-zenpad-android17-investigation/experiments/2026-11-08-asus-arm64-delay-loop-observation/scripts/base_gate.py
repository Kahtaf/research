from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];B=R/'source/base';sha=lambda b:hashlib.sha256(b).hexdigest()
c=(R.parent/'2026-11-08-asus-large-v2-udelay-boundary/consultation.txt').read_text()
ref=c.split('DELAY_REFERENCE\n',1)[1].split('\nTIMEX_REFERENCE',1)[0].strip()+'\n'
assert (B/'arch/arm64/lib/delay.c').read_text()==ref
ref_t=c.split('TIMEX_REFERENCE\n',1)[1].split('\nACCESSOR_REFERENCE',1)[0].strip()+'\n'
assert (B/'arch/arm64/include/asm/timex.h').read_text()==ref_t
h=(B/'arch/arm64/include/asm/arch_timer.h').read_text()
assert 'isb();\n\treturn arch_timer_reg_read_stable(cntvct_el0);' in h
assert '_val = timer_unstable_counter_workaround->read_##reg();' in h and '_val = read_sysreg(reg);' in h
cmd=(B/'out-provenance/arch/arm64/lib/.delay.o.cmd').read_text()
for name in ['arch/arm64/lib/delay.c','arch/arm64/include/asm/timex.h','arch/arm64/include/asm/arch_timer.h'] :assert name in cmd
assert '-O2' in cmd and '-fno-optimize-sibling-calls' in cmd and 'gcc-cross/aarch64-linux-gnu/13/include' in cmd
D=json.loads((R/'evidence/base-disassembly.json').read_text());assert D['__const_udelay'].count('<__delay>')==1
loop=D['__delay'];assert loop.count('cntvct_el0')==2 and loop.count('\tblr\t')==2 and '\tyield' in loop and '\tb.cc' in loop
adc=D['asus_p00a_pmic_adc'];battery=D['asus_p00a_battery_get_property']
def addr(d):return int(re.search(r'^([0-9a-f]+) <',d,re.M)[1],16)
def returns(d,t):return [int(m[1],16)+4 for m in re.finditer(r'^([0-9a-f]+):.*\bbl\s+[0-9a-f]+ <'+t+'>',d,re.M)]
ret=returns(adc,'__const_udelay');assert len(ret)==1
lines=adc.splitlines();j=next(j for j,l in enumerate(lines) if l.startswith(hex(ret[0]-4)[2:]+':'))
pre='\n'.join(lines[j-8:j]);assert '#0xa934' in pre and '#0x13, lsl #16' in pre
hooks=returns('\n'.join(lines[j-10:j]),'asus_capture_pmic_step');assert len(hooks)==1
voltage=[]
for v in returns(battery,'asus_p00a_pmic_adc'):
 lines2=battery.splitlines();k=next(k for k,l in enumerate(lines2) if l.startswith(hex(v-4)[2:]+':'))
 if 'w0, #0x6' in '\n'.join(lines2[k-5:k]) and 'w1, #0x5' in '\n'.join(lines2[k-5:k]):voltage.append(v)
assert len(voltage)==1
out=dict(status='PASS_BEFORE_EDIT_SOURCE_REFERENCE_AND_LINKED_GATE',reference_delay_sha256=sha(ref.encode()),actual_delay_sha256=sha((B/'arch/arm64/lib/delay.c').read_bytes()),reference_timex_sha256=sha(ref_t.encode()),actual_arch_timer_sha256=sha(h.encode()),compiler='GCC 13.3.0 Ubuntu, actual .delay.o.cmd and compile.h retained',loop='actual __const_udelay BL __delay; initial and per-condition ISB plus CNTVCT or optional selected function pointer',runtime_workaround_activation='UNPROVED',source_vs_reference='hash equality for delay.c and timex.h; scoped accessor fragment equality; ELF callflow checked separately, no C-vs-ELF byte comparison',route_offsets=dict(voltage_adc_return=voltage[0]-addr(battery),pmic_pre_hook_return=hooks[0]-addr(adc),pmic_const_return=ret[0]-addr(adc)),nominal=dict(xloops=1288500,lpj=52000,HZ=250,requested=((1288500*52000*250)&((1<<64)-1))>>32,runtime_lpj='not yet observed'))
(R/'evidence/base-provenance-gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
