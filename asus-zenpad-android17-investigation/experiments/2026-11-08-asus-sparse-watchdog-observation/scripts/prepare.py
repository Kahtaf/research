"""One bounded cold record unit from the actual inspected source."""
from pathlib import Path
import difflib,hashlib,json
R=Path(__file__).resolve().parents[1];B=R/'source/base'
i=json.loads((R/'evidence/identity.json').read_text());run=i['run_uuid']
prior=json.loads((R.parent/'2026-11-08-asus-sparse-observer-liveness/evidence/identity.json').read_text())
i.update(mode=f'ASUS49-MODE run={run} profile=sparse-wdt-v1 hot=disabled ordinary_printk=filtered delay=original-virtual',watchdog_prefix=f'ASUS49-WDT run={run} ',**{n:prior[n] for n in ['helper_prefix','helper_event_suffixes','helper_alarm_suffix','direct_markers']})
source={n:(B/n).read_text() for n in ['drivers/watchdog/mtk_wdt.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h']}
def replace(n,a,z):
 assert source[n].count(a)==1,(n,a)
 source[n]=source[n].replace(a,z)
n='arch/arm64/kernel/asus_entry_tag.h'
source[n]=source[n].replace(prior['run_uuid'],run).replace('profile=sparse-v1','profile=sparse-wdt-v1')
source[n]+='\n#define ASUS_SPARSE_WDT_PREFIX "'+i['watchdog_prefix']+'"\n'
n='include/linux/asus_retained_trace.h'
addition='''/* Cold watchdog facts only; no MMIO or timing in the recorder. */
enum asus_sparse_wdt_event {
 ASUS_WDT_PROBE, ASUS_WDT_ALLOC_ERROR, ASUS_WDT_MAP_ERROR,
 ASUS_WDT_WATCHDOG_ERROR, ASUS_WDT_REBOOT_ERROR, ASUS_WDT_RESTART_ERROR,
 ASUS_WDT_PM_ERROR, ASUS_WDT_RESET_ERROR, ASUS_WDT_STOP,
 ASUS_WDT_PROBE_DONE, ASUS_WDT_RESTART
};
#ifdef CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE
void asus_sparse_wdt_record(enum asus_sparse_wdt_event event, int rc,
 u32 first, u32 second, unsigned long caller);
#else
static inline void asus_sparse_wdt_record(enum asus_sparse_wdt_event event, int rc,
 u32 first, u32 second, unsigned long caller) { }
#endif

'''
replace(n,'struct task_struct;\n','struct task_struct;\n'+addition)
n='arch/arm64/kernel/asus_retained_trace.c'
replace(n,' if (!sparse_prefix(text, len, helper, sizeof(helper) - 1))', ''' if (sparse_prefix(text, len, ASUS_SPARSE_WDT_PREFIX,
                   sizeof(ASUS_SPARSE_WDT_PREFIX) - 1))
  return true;
 if (!sparse_prefix(text, len, helper, sizeof(helper) - 1))''')
emitter='''/* No printk, clocks, allocation, sleep, or hardware access on this path. */
void noinline notrace asus_sparse_wdt_record(enum asus_sparse_wdt_event event,
 int rc, u32 first, u32 second, unsigned long caller)
{
 char line[288];
 const char *site;
 unsigned int len;

 switch (event) {
 case ASUS_WDT_PROBE:
  len = scnprintf(line, sizeof(line), ASUS_SPARSE_WDT_PREFIX
   "event=probe route=mtk_wdt_probe caller=%016lx", caller);
  break;
 case ASUS_WDT_STOP:
  len = scnprintf(line, sizeof(line), ASUS_SPARSE_WDT_PREFIX
   "event=stop before=%08x after=%08x en_before=%u en_after=%u caller=%016lx",
   first, second, !!(first & 1U), !!(second & 1U), caller);
  break;
 case ASUS_WDT_PROBE_DONE:
  len = scnprintf(line, sizeof(line), ASUS_SPARSE_WDT_PREFIX
   "event=probe_done rc=%d req_mode=%08x req_irq_en=%08x", rc, first, second);
  break;
 case ASUS_WDT_RESTART:
  len = scnprintf(line, sizeof(line), ASUS_SPARSE_WDT_PREFIX
   "event=restart route=mtk_reset_handler caller=%016lx", caller);
  break;
 default:
  switch (event) {
  case ASUS_WDT_ALLOC_ERROR: site = "alloc"; break;
  case ASUS_WDT_MAP_ERROR: site = "map"; break;
  case ASUS_WDT_WATCHDOG_ERROR: site = "watchdog_register"; break;
  case ASUS_WDT_REBOOT_ERROR: site = "reboot_notifier"; break;
  case ASUS_WDT_RESTART_ERROR: site = "restart_handler"; break;
  case ASUS_WDT_PM_ERROR: site = "pm_notifier"; break;
  case ASUS_WDT_RESET_ERROR: site = "reset_controller"; break;
  default: return;
  }
  len = scnprintf(line, sizeof(line), ASUS_SPARSE_WDT_PREFIX
   "event=error site=%s rc=%d", site, rc);
 }
 asus_retained_trace_write(line, len);
}

'''
replace(n,'static void __init trace_init(bool early)\n',emitter+'static void __init trace_init(bool early)\n')
(R/'source/emitter.inc').write_text(emitter)
n='drivers/watchdog/mtk_wdt.c'
replace(n,'#include <linux/err.h>','#include <linux/asus_retained_trace.h>\n#include <linux/err.h>')
replace(n,'\tif (ret != 0)\n\t\tpr_err("could not register toprgu reset controller: %d\\n", ret);','''\tif (ret != 0) {
\t\tasus_sparse_wdt_record(ASUS_WDT_RESET_ERROR, ret, 0, 0, 0);
\t\tpr_err("could not register toprgu reset controller: %d\\n", ret);
\t}''')
replace(n,'\tmtk_wdt = container_of(this, struct mtk_wdt_dev, restart_handler);','''\tasus_sparse_wdt_record(ASUS_WDT_RESTART, 0, 0, 0,
\t\t(unsigned long)__builtin_return_address(0));
\tmtk_wdt = container_of(this, struct mtk_wdt_dev, restart_handler);''')
old='''\tu32 reg;

\treg = readl(wdt_base + WDT_MODE);
\treg &= ~WDT_MODE_EN;
\treg |= WDT_MODE_KEY;
\tiowrite32(reg, wdt_base + WDT_MODE);

\treturn 0;
}'''
new='''\tu32 reg, before, after;

\treg = readl(wdt_base + WDT_MODE);
\tbefore = reg;
\treg &= ~WDT_MODE_EN;
\treg |= WDT_MODE_KEY;
\tiowrite32(reg, wdt_base + WDT_MODE);
\tafter = readl(wdt_base + WDT_MODE);
\tasus_sparse_wdt_record(ASUS_WDT_STOP, 0, before, after,
\t\t(unsigned long)__builtin_return_address(0));

\treturn 0;
}'''
replace(n,old,new)
replace(n,'\tunsigned int tmp;\n\tint err;\n\n\tmtk_wdt = devm_kzalloc', '''\tunsigned int tmp;
\tu32 req_mode, req_irq_en;
\tint err;

\tasus_sparse_wdt_record(ASUS_WDT_PROBE, 0, 0, 0,
\t\t(unsigned long)__builtin_return_address(0));
\tmtk_wdt = devm_kzalloc''')
replace(n,'\tif (!mtk_wdt)\n\t\treturn -ENOMEM;','''\tif (!mtk_wdt) {
\t\tasus_sparse_wdt_record(ASUS_WDT_ALLOC_ERROR, -ENOMEM, 0, 0, 0);
\t\treturn -ENOMEM;
\t}''')
replace(n,'\tif (IS_ERR(mtk_wdt->wdt_base))\n\t\treturn PTR_ERR(mtk_wdt->wdt_base);','''\tif (IS_ERR(mtk_wdt->wdt_base)) {
\t\tasus_sparse_wdt_record(ASUS_WDT_MAP_ERROR,
\t\t\tPTR_ERR(mtk_wdt->wdt_base), 0, 0, 0);
\t\treturn PTR_ERR(mtk_wdt->wdt_base);
\t}''')
replace(n,'\tif (unlikely(err))\n\t\treturn err;','''\tif (unlikely(err)) {
\t\tasus_sparse_wdt_record(ASUS_WDT_WATCHDOG_ERROR, err, 0, 0, 0);
\t\treturn err;
\t}''')
for call,event in [('register_reboot_notifier','REBOOT'),('register_restart_handler','RESTART')]:
 start=source[n].index('\t\terr = '+call+'(');end=source[n].index('\n\t}',start)
 block=source[n][start:end]
 z=block.replace('\t\tif (err != 0)\n','\t\tif (err != 0) {\n\t\t\tasus_sparse_wdt_record(ASUS_WDT_'+event+'_ERROR, err, 0, 0, 0);\n')+'\n\t\t}'
 replace(n,block,z)
replace(n,'\tif (err)\n\t\tdev_warn(&pdev->dev,"[%s] failed to register WDT PM notifier %d\\n",\n\t\t\t__func__, err);','''\tif (err) {
\t\tasus_sparse_wdt_record(ASUS_WDT_PM_ERROR, err, 0, 0, 0);
\t\tdev_warn(&pdev->dev,"[%s] failed to register WDT PM notifier %d\\n",
\t\t\t__func__, err);
\t}''')
replace(n,'\trtc_mark_quiescent(0);\n\n\treturn 0;','''\trtc_mark_quiescent(0);

\t/* These configuration registers already use read/modify/write above. */
\treq_mode = ioread32(mtk_wdt->wdt_base + WDT_REQ_MODE);
\treq_irq_en = ioread32(mtk_wdt->wdt_base + WDT_REQ_IRQ_EN);
\tasus_sparse_wdt_record(ASUS_WDT_PROBE_DONE, 0, req_mode, req_irq_en, 0);
\treturn 0;''')
pins={};patch=[]
for n,s in source.items():
 old=(B/n).read_bytes();p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=hashlib.sha256(old).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest())
 patch+=difflib.unified_diff(old.decode().splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n)
(R/'source/changes.patch').write_text(''.join(patch))
(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
print(json.dumps({'UUID':run,'changed':list(pins),'patch_lines':len(patch)},indent=2))
