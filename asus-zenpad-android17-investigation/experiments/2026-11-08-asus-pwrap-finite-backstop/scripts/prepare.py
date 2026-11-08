from pathlib import Path
import difflib,hashlib,json,shutil,uuid
R=Path(__file__).resolve().parents[1];S=R/'source';B=S/'base'
files=['drivers/soc/mediatek/mtk-pmic-wrap.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','drivers/power/supply/mediatek/battery/battery_common.c']
assert not (R/'evidence/prepost.json').exists()
for n in files:
 p=S/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((B/n).read_bytes())
def edit(n,a,z):
 p=S/n;s=p.read_text();assert s.count(a)==1,(n,a);p.write_text(s.replace(a,z))
kid=str(uuid.uuid4());i=dict(kernel_uuid=kid,base_remote='/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50',remote_root='/srv/android/asus-pwrap-finite-backstop-20261108-'+kid[:8],helper_uuid='ef56ad88-6904-4452-90a1-3744beaa3c78',control_uuid='342c9034-6b6f-4d95-aa67-9228b0904eb2',budget=16777216)
n='arch/arm64/kernel/asus_entry_tag.h';s=(S/n).read_text().replace('e7acab50-e05a-4684-8e5a-c352f025564b',kid).replace('profile=devkmsg-boundary-v1 format=1','profile=pwrap-finite-v1 format=1 poll_budget=16777216');s+='\n#define ASUS_PWRAP_PREFIX "ASUS49-PWRAP run='+kid+' v=1 "\n';(S/n).write_text(s);i['mode']=next(l.split('"')[1] for l in s.splitlines() if l.startswith('#define ASUS_SPARSE_MODE'))
(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
n='arch/arm64/kernel/asus_retained_trace.c'
edit(n,' if (sparse_prefix(text, len, ASUS_DEVKMSG_PREFIX,',' if (sparse_prefix(text, len, ASUS_PWRAP_PREFIX,\n                   sizeof(ASUS_PWRAP_PREFIX) - 1))\n  return true;\n if (sparse_prefix(text, len, ASUS_DEVKMSG_PREFIX,')
n='include/linux/asus_retained_trace.h'
edit(n,'struct task_struct;','''struct task_struct;
/* Built-in pwrap diagnostic; caller must have returned from the ADC path. */
#ifdef CONFIG_MTK_PMIC_WRAP
void asus_pwrap_backstop_publish(void);
#else
static inline void asus_pwrap_backstop_publish(void) { }
#endif''')
n='drivers/power/supply/mediatek/battery/battery_common.c'
edit(n,'#include <linux/power/asus_p00a_battery.h>','#include <linux/power/asus_p00a_battery.h>\n#include <linux/asus_retained_trace.h>')
edit(n,'\treturn asus_p00a_battery_get_property(psp, val);','''\tret = asus_p00a_battery_get_property(psp, val);
	/* The diagnostic callback has released ADC and regmap serialization. */
	asus_pwrap_backstop_publish();
	return ret;''')
n='drivers/soc/mediatek/mtk-pmic-wrap.c'
edit(n,'#include <linux/clk.h>','#include <linux/clk.h>\n#include <linux/asus_retained_trace.h>\n#include <linux/preempt.h>\n#include "../../../arch/arm64/kernel/asus_entry_tag.h"')
# Header identity is already used by the exact ARM64 retained writer. This candidate is ARM64 only.
record='''/*
 * 2.5 GHz is the MT8163 clock driver's PLL ceiling; supported CPU OPPs
 * reach 1.5 GHz plus <=10% turbo. Cortex-A53 issues at most two insns/cycle.
 * Exact linked not-ready iteration: >=48 insns, counting sched_clock and
 * the WACS2 read, assuming ZERO bus/counter/cache/barrier delay. Therefore
 * <=ceil(10ms * 2.5GHz * 2 / 48) = 1041667 iterations per 10ms.
 * 2^24 gives >16x headroom. This count is NOT elapsed time. Assumes this
 * supported execution envelope, returning individual reads and acquired
 * locks; see the pinned derivation and candidate ELF instruction proof.
 */
#define PWRAP_POLL_BUDGET 16777216U

#ifdef CONFIG_MTK_PMIC_WRAP
/* 0 empty, 1 first winner writing, 2 release-published, 3 drain claimed.
 * No retained writer, clocks, MMIO, allocation or extra locks here.
 */
static struct {
	unsigned long long start, last;
	u32 iterations, wait_id, ready;
	int result;
} pwrap_backstop;
static int pwrap_backstop_state;

static void pwrap_backstop_record(unsigned long long start,
		unsigned long long last, u32 iterations,
		bool (*fp)(struct pmic_wrapper *), bool ready)
{
	if (cmpxchg(&pwrap_backstop_state, 0, 1) != 0)
		return;
	pwrap_backstop.start = start;
	pwrap_backstop.last = last;
	pwrap_backstop.iterations = iterations;
	pwrap_backstop.wait_id = fp == pwrap_is_fsm_idle ? 1 :
		(fp == pwrap_is_fsm_vldclr ? 2 : 0);
	pwrap_backstop.ready = ready;
	pwrap_backstop.result = ready ? 0 : -ETIMEDOUT;
	smp_store_release(&pwrap_backstop_state, 2);
}

/* Called only after the battery property callback returns. Never publish
 * under the ADC/regmap IRQ-save locks. Refusal leaves publication UNKNOWN.
 */
void noinline notrace asus_pwrap_backstop_publish(void)
{
	char line[224];
	unsigned int n;

	if (!in_task() || in_atomic() || irqs_disabled())
		return;
	if (smp_load_acquire(&pwrap_backstop_state) != 2 ||
	    cmpxchg(&pwrap_backstop_state, 2, 3) != 2)
		return;
	n = scnprintf(line, sizeof(line), ASUS_PWRAP_PREFIX
		"EXHAUST start=%llu last=%llu iterations=%u wait=%u ready=%u rc=%d",
		pwrap_backstop.start, pwrap_backstop.last,
		pwrap_backstop.iterations, pwrap_backstop.wait_id,
		pwrap_backstop.ready, pwrap_backstop.result);
	asus_retained_trace_write(line, n);
}
#else
static inline void pwrap_backstop_record(unsigned long long start,
		unsigned long long last, u32 iterations,
		bool (*fp)(struct pmic_wrapper *), bool ready) { }
#endif

'''
edit(n,'static int pwrap_timeout_ns(unsigned long long start_time_ns, unsigned long long timeout_time_ns)',record+'static int pwrap_timeout_ns(unsigned long long start_time_ns, unsigned long long timeout_time_ns,\n\t\tunsigned long long *last_clock)')
edit(n,'\tcur_time = sched_clock();\t/* ns */','\tcur_time = sched_clock();\t/* ns */\n\t*last_clock = cur_time;')
edit(n,'\tunsigned long long start_time_ns = 0, timeout_ns = 0;','\tunsigned long long start_time_ns = 0, timeout_ns = 0, last_clock;\n\tu32 remaining = PWRAP_POLL_BUDGET;\n\tbool ready;')
edit(n,'\t\tif (pwrap_timeout_ns(start_time_ns, timeout_ns))','\t\tif (pwrap_timeout_ns(start_time_ns, timeout_ns, &last_clock))')
edit(n,'\t\tif (fp(wrp))\n\t\t\treturn 0;\n\t} while (1);','''		if (fp(wrp))
			return 0;
		if (!--remaining) {
			ready = fp(wrp);
			pwrap_backstop_record(start_time_ns, last_clock,
				PWRAP_POLL_BUDGET, fp, ready);
			return ready ? 0 : -ETIMEDOUT;
		}
	} while (1);''')
patch='';pins={}
for n in files:
 a=(B/n).read_bytes();z=(S/n).read_bytes();pins[n]=dict(before=hashlib.sha256(a).hexdigest(),after=hashlib.sha256(z).hexdigest())
 patch+=''.join(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n))
(S/'changes.patch').write_text(patch);(R/'evidence/prepost.json').write_text(json.dumps(pins,indent=2)+'\n')
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:shutil.copy2(R.parent/'2026-11-08-asus-devkmsg-return-boundary/source'/n,S/n)
print(json.dumps(i,indent=2))
