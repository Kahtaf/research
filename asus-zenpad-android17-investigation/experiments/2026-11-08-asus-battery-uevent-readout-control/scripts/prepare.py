from pathlib import Path
import difflib,hashlib,json,shutil,uuid,gzip,re
R=Path(__file__).resolve().parents[1];S=R/'source';B=S/'base';E=R/'evidence'
files=['drivers/power/supply/power_supply_core.c','drivers/power/supply/power_supply_sysfs.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h']
assert not (E/'identity.json').exists()
for n in files:
 p=S/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((B/n).read_bytes())
def edit(n,a,z):
 p=S/n;s=p.read_text();assert s.count(a)==1,(n,a);p.write_text(s.replace(a,z))
kid=str(uuid.uuid4());i=dict(kernel_uuid=kid,base_remote='/srv/android/asus-pwrap-finite-backstop-20261108-09abbded',remote_root='/srv/android/asus-battery-uevent-readout-20261108-'+kid[:8],helper_uuid='ef56ad88-6904-4452-90a1-3744beaa3c78',control_uuid='342c9034-6b6f-4d95-aa67-9228b0904eb2',budget=16777216,battery_name='battery')
n='arch/arm64/kernel/asus_entry_tag.h';s=(S/n).read_text().replace('09abbded-4301-486b-8945-b8748248f2d2',kid).replace('profile=pwrap-finite-v1 format=1','profile=battery-uevent-omit-v1 format=1');s+='\n#define ASUS_BATTERY_UEVENT_PREFIX "ASUS49-BUEV run='+kid+' v=1 "\n';(S/n).write_text(s);i['mode']=next(l.split('"')[1] for l in s.splitlines() if l.startswith('#define ASUS_SPARSE_MODE'))
(E/'identity.json').write_text(json.dumps(i,indent=2)+'\n')
edit('include/linux/asus_retained_trace.h','struct task_struct;','''struct task_struct;
struct power_supply;
/* One scoped battery uevent omission record, not a property drain. */
bool asus_battery_uevent_begin(struct power_supply *psy);
void asus_battery_uevent_publish(bool armed, int result);''')
n='drivers/power/supply/power_supply_sysfs.c'
edit(n,'#include <linux/ctype.h>','''#include <linux/asus_retained_trace.h>
#include <linux/atomic.h>
#include <linux/preempt.h>
#include <linux/sched.h>
#include "../../../arch/arm64/kernel/asus_entry_tag.h"
#include <linux/ctype.h>''')
record='''/* One worker call owns this diagnostic slot. Registration-time omissions
 * still count, but cannot be mistaken for the scoped KOBJ_CHANGE call.
 * States: 0 unused, 1 preparing, 2 armed, 3 first hit writing,
 * 4 first hit release-published, 5 publication claimed (no retry).
 * The numeric owner is internal only; no addresses or names are recorded.
 */
static atomic_t battery_uevent_omissions = ATOMIC_INIT(0);
static struct {
	u32 before, first;
	pid_t owner;
} battery_uevent_skip;
static int battery_uevent_state;

bool noinline notrace asus_battery_uevent_begin(struct power_supply *psy)
{
	if (strcmp(psy->desc->name, "battery") ||
	    cmpxchg(&battery_uevent_state, 0, 1) != 0)
		return false;
	battery_uevent_skip.owner = task_pid_nr(current);
	battery_uevent_skip.before = (u32)atomic_read(&battery_uevent_omissions);
	smp_store_release(&battery_uevent_state, 2);
	return true;
}

static void battery_uevent_omitted(void)
{
	u32 count = (u32)atomic_inc_return(&battery_uevent_omissions);

	if (smp_load_acquire(&battery_uevent_state) != 2 ||
	    battery_uevent_skip.owner != task_pid_nr(current) ||
	    cmpxchg(&battery_uevent_state, 2, 3) != 2)
		return;
	battery_uevent_skip.first = count;
	smp_store_release(&battery_uevent_state, 4);
}

/* Only the owning worker calls this after its actual kobject_uevent return,
 * before the original changed_lock reacquisition. Claim before context checks
 * so a refused writer is not retried. An undrained/refused record is UNKNOWN.
 */
void noinline notrace asus_battery_uevent_publish(bool armed, int result)
{
	char line[192];
	u32 after;
	unsigned int n;

	if (!armed || smp_load_acquire(&battery_uevent_state) != 4 ||
	    battery_uevent_skip.owner != task_pid_nr(current) ||
	    cmpxchg(&battery_uevent_state, 4, 5) != 4)
		return;
	after = (u32)atomic_read(&battery_uevent_omissions);
	if (!in_task() || in_atomic() || irqs_disabled() ||
	    battery_uevent_skip.first <= battery_uevent_skip.before ||
	    battery_uevent_skip.first > after)
		return;
	n = scnprintf(line, sizeof(line), ASUS_BATTERY_UEVENT_PREFIX
		"SKIP first=%u before=%u after=%u same_task=1 uevent_rc=%d",
		battery_uevent_skip.first, battery_uevent_skip.before, after, result);
	asus_retained_trace_write(line, n);
}

'''
edit(n,'int power_supply_uevent(struct device *dev, struct kobj_uevent_env *env)',record+'int power_supply_uevent(struct device *dev, struct kobj_uevent_env *env)')
edit(n,'\tprop_buf = (char *)get_zeroed_page(GFP_KERNEL);','''	if (!strcmp(psy->desc->name, "battery")) {
		battery_uevent_omitted();
		return 0;
	}

	prop_buf = (char *)get_zeroed_page(GFP_KERNEL);''')
n='drivers/power/supply/power_supply_core.c'
edit(n,'\tint capture_ret;\n\tstruct power_supply *psy = container_of(work,','\tint capture_ret;\n\tbool battery_uevent_armed;\n\tstruct power_supply *psy = container_of(work,')
edit(n,'\t\tcapture_ret = kobject_uevent(&psy->dev.kobj, KOBJ_CHANGE);','''		battery_uevent_armed = asus_battery_uevent_begin(psy);
		capture_ret = kobject_uevent(&psy->dev.kobj, KOBJ_CHANGE);
		asus_battery_uevent_publish(battery_uevent_armed, capture_ret);''')
edit('arch/arm64/kernel/asus_retained_trace.c',' if (sparse_prefix(text, len, ASUS_PWRAP_PREFIX,',' if (sparse_prefix(text, len, ASUS_BATTERY_UEVENT_PREFIX,\n                   sizeof(ASUS_BATTERY_UEVENT_PREFIX) - 1))\n  return true;\n if (sparse_prefix(text, len, ASUS_PWRAP_PREFIX,')
pins={};patch=''
for n in files:
 a=(B/n).read_bytes();z=(S/n).read_bytes();pins[n]=dict(before=hashlib.sha256(a).hexdigest(),after=hashlib.sha256(z).hexdigest());patch+=''.join(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n))
(S/'changes.patch').write_text(patch);(E/'prepost.json').write_text(json.dumps(pins,indent=2)+'\n')
# Bounded inventory: six production files plus selected config and genuine map.
scopes={
'drivers/power/supply/power_supply_core.c':[(65,81),(83,144),(530,550),(610,650)],
'drivers/power/supply/power_supply_sysfs.c':[(78,92),(305,361)],
'drivers/power/supply/mediatek/battery/battery_common.c':[(305,326),(591,612),(788,803),(3631,3673),(3738,3769),(4838,4848)],
'drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c':[(68,136)],
'drivers/power/supply/mediatek/battery/battery_meter.c':[(2738,2750),(2837,2845),(3141,3160)],
'drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c':[(30,96),(119,135)]}
for n,ranges in scopes.items():
 d=(B/n).read_bytes();lines=d.decode().splitlines();p=E/'caller-slices'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(f'{j}: {lines[j-1]}\n' for a,z in ranges for j in range(a,min(z,len(lines))+1)))
(E/'caller-selected.config').write_text('\n'.join(x for x in (E/'base.config').read_text().splitlines() if re.match(r'CONFIG_(ASUS_P00A|MTK_SMART_BATTERY|POWER_SUPPLY|THERMAL)',x))+'\n')
m=gzip.decompress((E/'base-System.map.gz').read_bytes()).decode();(E/'caller-selected-System.map').write_text('\n'.join(x for x in m.splitlines() if any(t in x.split()[-1] for t in ['battery_get_property','battery_read_sample','power_supply_read_temp','power_supply_uevent','power_supply_changed_work','bat_thread_kthread','BAT_thread','battery_meter_get_battery_voltage','asus_p00a_soc_update','external_power_changed','p00a_monitor','p00a_apply','asus_p00a_pmic_adc']))+'\n')
(E/'caller-inventory-pins.json').write_text(json.dumps({n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in scopes},indent=2)+'\n')
(E/'CALLER-INVENTORY.md').write_text('''# Bounded pre-build inventory and limits

Six production files, selected resolved config and genuine baseline System.map (eight inputs); exact source pins and numbered slices accompany this report. Diagnostic plumbing is separate from this caller inventory. No whole power-stack audit.

Selected CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC=y and MAIN_BATTERY_SOC=y; battery_common.c battery_main.psd.name is exactly "battery", with battery_get_property dispatching directly to asus_p00a_battery_get_property. The descriptor includes TEMP and batt_vol. battery_diag.c voltage/batt_vol uses asus_p00a_pmic_adc(6,5); battery_read_sample independently uses (6,5). These native functions exist in genuine System.map.

The worker's class_for_each_device still calls each supplied device's external_power_changed callback before kobject_uevent. The battery descriptor inspected here has no external_power_changed member. The selected BQ25896 driver includes control.h/charge_snapshot.inc/battery_status.inc and runs p00a_monitor -> p00a_apply under its original lock. Exact callbacks/indirect read paths inside those includes were outside this bound; no claim that charger traffic cannot reach channel 6. This is an explicit route gap, not an absent-reader proof.

Thermal: power_supply_read_temp -> power_supply_get_property(TEMP) -> battery_get_property -> diagnostic property implementation. psy_register_thermal registers for TEMP unless no_thermal; the battery descriptor has no no_thermal override. TEMP uses channel 5 with five samples plus presence traffic, not channel 6 in the inspected body. Actual runtime zone registration/poll occurrence is unknown. This read path is preserved.

Battery worker: selected BAT_thread -> asus_p00a_soc_update -> asus_p00a_soc_read; bat_thread_kthread calls BAT_thread under its original conditions, and is launched by battery_probe. Selected battery_meter oam_init/oam_run also call soc_update; the function is linked. The asus_p00a_soc.inc internals were not acquired, so the complete soc_update -> read_sample dynamic route is an exact gap. Independently linked battery_read_sample contains channel 6/five samples. Legacy battery_meter_get_battery_voltage -> battery_meter_ctrl(GET_ADC_V_BAT_SENSE) is present, but its selected runtime control target was not traced here; do not equate its legacy name with proof of this diagnostic channel-6 route.

Sysfs power_supply_show_property continues to call the getter. No other caller is suppressed. Runtime scheduling, included charger/SOC internals and other indirect readers remain possible; a missing or negative omission result cannot exonerate AUXADC, PMIC transport, other readers, or reporting. This inventory is sufficient to bound interpretation and does not authorize another audit or change.
''')
print(json.dumps(i,indent=2))
