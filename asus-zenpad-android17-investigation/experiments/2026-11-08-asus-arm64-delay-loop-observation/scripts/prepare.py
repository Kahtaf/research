from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[1];B=R/'source/base';i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid'];old='a1ff82b1-3e45-4f05-8c99-7112204d3981'
gate=json.loads((R/'evidence/base-provenance-gate.json').read_text());assert gate['status'].startswith('PASS_BEFORE_EDIT')
n='arch/arm64/lib/delay.c';s=(B/n).read_text();s=s.replace('#include <linux/timex.h>','#include <linux/timex.h>\n#include <linux/asus_retained_trace.h>')
a=s.index('void __delay(');z=s.index('EXPORT_SYMBOL(__delay);',a)
s=s[:a]+'''void __delay(unsigned long cycles)
{
	cycles_t start, counter;
	u64 iteration = 0;
	u64 generation = asus_capture_delay_begin(cycles,
		(unsigned long)__builtin_return_address(0));

	if (generation)
		asus_capture_delay_point(generation, 0, 0, 0, cycles);
	start = get_cycles();
	if (generation)
		asus_capture_delay_point(generation, 1, 0, start, cycles);
	for (;;) {
		counter = get_cycles();
		if (generation) {
			if (iteration != U64_MAX) {
				++iteration;
				if (iteration == U64_MAX)
					asus_capture_delay_point(generation, 7, iteration, counter, cycles);
			}
			if (iteration == 1)
				asus_capture_delay_point(generation, 2, iteration, counter, cycles);
			else if (iteration == 256)
				asus_capture_delay_point(generation, 3, iteration, counter, cycles);
			else if (iteration == 65536)
				asus_capture_delay_point(generation, 4, iteration, counter, cycles);
			else if (iteration == 1048576)
				asus_capture_delay_point(generation, 5, iteration, counter, cycles);
		}
		if ((counter - start) >= cycles)
			break;
		cpu_relax();
	}
	if (generation)
		asus_capture_delay_point(generation, 6, iteration, counter, cycles);
}
'''+s[z:]
s=s.replace('unsigned long loops;','unsigned long loops, lpj;').replace('loops = xloops * loops_per_jiffy * HZ;','lpj = loops_per_jiffy;\n\tloops = xloops * lpj * HZ;\n\tasus_capture_delay_calc(xloops, lpj, HZ, loops, loops >> 32,\n\t\t(unsigned long)__builtin_return_address(0));')
files={n:s}
n='include/linux/asus_retained_trace.h';s=(B/n).read_text();s=s.replace('struct task_struct;', 'struct task_struct;\n'+(R/'source/delay-interface.inc').read_text(),1);files[n]=s
n='arch/arm64/kernel/asus_entry_tag.h';s=(B/n).read_text().replace(old,u);files[n]=s;i['tag']=s.split('"')[1].replace('\\n','\n');i['capture_tag']='A49CAP1 uuid='+u
n='arch/arm64/kernel/asus_retained_trace.c';s=(B/n).read_text().replace(old,u)
s=s.replace('#include <linux/asus_retained_trace.h>','#include <linux/asus_retained_trace.h>\n#include <linux/delay.h>\n#include <linux/power/asus_p00a_battery.h>',1)
s=s.replace('static noinline void pm_record(', 'static void dl_pmic(const u64 *f, unsigned long hook);\n\nstatic noinline void pm_record(',1)
s=s.replace('int sample, int poll, u32 status, bool begin)','int sample, int poll, u32 status, bool begin, unsigned long hook)',1)
a=s.index('static noinline void pm_record(');z=s.index('static void __init cap_init(',a)
part=s[a:z].replace(' pm_header();\nout:', ' pm_header();\n if (code == 38 || code == 39)\n  dl_pmic(f, hook);\nout:',1).replace('0x80000000U, true);','0x80000000U, true, 0);',1).replace('status, false);','status, false,\n   (unsigned long)__builtin_return_address(0));',1)
s=s[:a]+part+s[z:]
dl=(R/'source/delay_capture.inc').read_text().replace('UUID',u)
for a,k in [('VOLTAGE_RETURN','voltage_adc_return'),('PRE_RETURN','pmic_pre_hook_return'),('CONST_RETURN','pmic_const_return')]:dl=dl.replace(a,str(gate['route_offsets'][k]))
s=s.replace('static void __init cap_init(',dl+'\nstatic void __init cap_init(',1)
a=s.index('static void __init cap_init(');z=s.index('static bool cap_lock(',a);part=s[a:z]
part=part.replace(' BUILD_BUG_ON(PM_SIZE % 64);',' BUILD_BUG_ON(PM_SIZE % 64);\n BUILD_BUG_ON(DL_SIZE % 64);').replace('CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE + DL_SIZE')
part=part.replace(' pm_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);',' pm_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);\n dl_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE);')
part=part.replace(' smp_store_release(&pm_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);',' smp_store_release(&pm_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);\n smp_store_release(&dl_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE);')
s=s[:a]+part+s[z:];files[n]=s
pins={};diff=[]
for n,s in files.items():
 b=(B/n).read_bytes();p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=hashlib.sha256(b).hexdigest(),after=hashlib.sha256(s.encode()).hexdigest());diff.extend(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
preserved={n:v for n,v in json.loads((R/'evidence/actual-base.json').read_text())['source_pins'].items() if n not in pins and not n.startswith('out-provenance/')}
(R/'evidence/preserved-source-pins.json').write_text(json.dumps(preserved,indent=2)+'\n')
print('Prepared exactly four changed kernel files after passing provenance gate')
