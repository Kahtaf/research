from pathlib import Path
import json,hashlib,difflib,re
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-07-asus-linux49-work-dispatch-capture'
i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid'];old_uuid='b4702f9a-6b32-423f-b789-d2bd515c0707'
sha=lambda d:hashlib.sha256(d).hexdigest()
names=['drivers/power/supply/power_supply_core.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h']
pins={};diff=[]
for n in names:
 old=(R/'source/base'/n).read_text();s=old
 if n.endswith('power_supply_core.c'):
  s=s.replace('#include <linux/module.h>','#include <linux/asus_retained_trace.h>\n#include <linux/module.h>',1)
  a='\tstruct power_supply *pst = dev_get_drvdata(dev);';s=s.replace(a,a+'\n\tstruct asus_ps_capture capture;',1)
  a='\t\tif (pst->desc->external_power_changed)\n\t\t\tpst->desc->external_power_changed(pst);'
  z='''\t\tif (pst->desc->external_power_changed) {
\t\t\tasus_capture_ps_begin(&capture, 50, 0, (unsigned long)pst,
\t\t\t\tpst->desc->name,
\t\t\t\t(unsigned long)READ_ONCE(pst->desc->external_power_changed),
\t\t\t\t0, (unsigned long)psy, psy->desc->name);
\t\t\tpst->desc->external_power_changed(pst);
\t\t\tasus_capture_ps_step(&capture, 51, 0, U64_MAX);
\t\t}'''
  assert s.count(a)==1;s=s.replace(a,z)
  a=s.index('static void power_supply_changed_work(');z=s.index('\nvoid power_supply_changed(',a);f=s[a:z]
  f=f.replace('\tunsigned long flags;','\tunsigned long flags;\n\tstruct asus_ps_capture capture;\n\tint capture_ret;',1)
  marker='\tdev_dbg('
  pos=f.index(marker)
  f=f[:pos]+'''\tasus_capture_ps_begin(&capture, 1, (unsigned long)work,
\t\t(unsigned long)psy, psy->desc->name, 0, READ_ONCE(psy->changed), 0, NULL);
'''+f[pos:]
  marker='\tspin_lock_irqsave(&psy->changed_lock, flags);'
  f=f.replace(marker,'\tasus_capture_ps_step(&capture, 2, 0, U64_MAX);\n'+marker+'\n\tasus_capture_ps_step(&capture, 3, READ_ONCE(psy->changed), U64_MAX);',1)
  f=f.replace('\t\tpsy->changed = false;','\t\tpsy->changed = false;\n\t\tasus_capture_ps_step(&capture, 4, 0, U64_MAX);',1)
  f=f.replace('\t\tspin_unlock_irqrestore(&psy->changed_lock, flags);','\t\tspin_unlock_irqrestore(&psy->changed_lock, flags);\n\t\tasus_capture_ps_step(&capture, 5, 0, U64_MAX);',1)
  f=f.replace('\t\tclass_for_each_device(', '\t\tasus_capture_ps_step(&capture, 6, 0, U64_MAX);\n\t\tcapture_ret = class_for_each_device(',1)
  f=f.replace('\t\t\t\t      __power_supply_changed_work);','\t\t\t\t      __power_supply_changed_work);\n\t\tasus_capture_ps_step(&capture, 7, 0, (u32)capture_ret);',1)
  f=f.replace('\t\tpower_supply_update_leds(psy);','\t\tasus_capture_ps_step(&capture, 8, 0, U64_MAX);\n\t\tpower_supply_update_leds(psy);\n\t\tasus_capture_ps_step(&capture, 9, 0, U64_MAX);',1)
  f=f.replace('\t\tatomic_notifier_call_chain(', '\t\tasus_capture_ps_step(&capture, 10, 0, U64_MAX);\n\t\tcapture_ret = atomic_notifier_call_chain(',1)
  f=f.replace('\t\t\t\tPSY_EVENT_PROP_CHANGED, psy);','\t\t\t\tPSY_EVENT_PROP_CHANGED, psy);\n\t\tasus_capture_ps_step(&capture, 11, 0, (u32)capture_ret);',1)
  f=f.replace('\t\tkobject_uevent(&psy->dev.kobj, KOBJ_CHANGE);','\t\tasus_capture_ps_step(&capture, 12, 0, U64_MAX);\n\t\tcapture_ret = kobject_uevent(&psy->dev.kobj, KOBJ_CHANGE);\n\t\tasus_capture_ps_step(&capture, 13, 0, (u32)capture_ret);',1)
  marker='\t\tspin_lock_irqsave(&psy->changed_lock, flags);\n\t}'
  assert f.count(marker)==1
  f=f.replace(marker,'\t\tasus_capture_ps_step(&capture, 14, 0, U64_MAX);\n\t\tspin_lock_irqsave(&psy->changed_lock, flags);\n\t\tasus_capture_ps_step(&capture, 15, READ_ONCE(psy->changed), U64_MAX);\n\t} else {\n\t\tasus_capture_ps_step(&capture, 21, 0, U64_MAX);\n\t}',1)
  marker='\tif (likely(!psy->changed))\n\t\tpm_relax(&psy->dev);\n\tspin_unlock_irqrestore(&psy->changed_lock, flags);'
  z='''\tasus_capture_ps_step(&capture, 16, READ_ONCE(psy->changed), U64_MAX);
\tif (likely(!psy->changed)) {
\t\tasus_capture_ps_step(&capture, 17, 0, U64_MAX);
\t\tpm_relax(&psy->dev);
\t\tasus_capture_ps_step(&capture, 18, 0, U64_MAX);
\t}
\tasus_capture_ps_step(&capture, 19, 0, U64_MAX);
\tspin_unlock_irqrestore(&psy->changed_lock, flags);
\tasus_capture_ps_step(&capture, 20, 0, U64_MAX);'''
  assert f.count(marker)==1;f=f.replace(marker,z)
  s=s[:a]+f+s[s.index('\nvoid power_supply_changed(',a):]
  a=s.index('int power_supply_get_property(');z=s.index('EXPORT_SYMBOL_GPL(power_supply_get_property);',a);f=s[a:z]
  f=f.replace('{\n','{\n\tstruct asus_ps_capture capture;\n\tint capture_ret;\n\n',1)
  marker='\treturn psy->desc->get_property(psy, psp, val);'
  z='''\tasus_capture_ps_begin(&capture, 40, 0, (unsigned long)psy,
\t\tpsy->desc->name, (unsigned long)READ_ONCE(psy->desc->get_property),
\t\t(u32)psp, 0, NULL);
\tcapture_ret = psy->desc->get_property(psy, psp, val);
\tasus_capture_ps_step(&capture, 41, (u32)psp, (u32)capture_ret);
\treturn capture_ret;'''
  assert f.count(marker)==1;f=f.replace(marker,z)
  s=s[:a]+f+s[s.index('EXPORT_SYMBOL_GPL(power_supply_get_property);',a):]
 elif n.endswith('asus_retained_trace.h'):
  s=s.replace('struct task_struct;','struct task_struct;\n'+(R/'source/ps-interface.inc').read_text(),1)
 elif n.endswith('asus_retained_trace.c'):
  s=s.replace(old_uuid,u)
  marker='static void __init cap_init(';assert s.count(marker)==1
  s=s.replace(marker,(R/'source/ps_capture.inc').read_text().replace('UUID',u)+marker,1)
  s=s.replace(' BUILD_BUG_ON(WD_SIZE % 64);',' BUILD_BUG_ON(WD_SIZE % 64);\n BUILD_BUG_ON(PS_SIZE % 64);',1)
  a=s.index('static void __init cap_init(');z=s.index('static bool cap_lock(',a);f=s[a:z]
  f=f.replace('CAP_SIZE + SW_SIZE + WD_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE')
  f=f.replace(' wd_init(dest + CAP_SIZE + SW_SIZE);',' wd_init(dest + CAP_SIZE + SW_SIZE);\n ps_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE);')
  f=f.replace(' smp_store_release(&wd_area, dest + CAP_SIZE + SW_SIZE);',' smp_store_release(&wd_area, dest + CAP_SIZE + SW_SIZE);\n smp_store_release(&ps_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE);')
  s=s[:a]+f+s[z:]
 else:
  s=s.replace(old_uuid,u).replace('a3ce18e1e0d1f38307a2a63e783af3cb2b633c26a706366e6714b24ae36302b4',i['base_compiled_sha256'])
  i['tag']=s.split('"')[1].replace('\\n','\n');i['capture_tag']='A49CAP1 uuid='+u
 assert s!=old
 p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=sha(old.encode()),after=sha(s.encode()))
 diff.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
p=json.loads((B/'evidence/preserved-source-pins.json').read_text());p['kernel/workqueue.c']=sha((R/'source/base/kernel/workqueue.c').read_bytes());p['include/linux/power_supply.h']=sha((R/'source/base/include/linux/power_supply.h').read_bytes())
(R/'evidence/preserved-source-pins.json').write_text(json.dumps(p,indent=2)+'\n')
print(json.dumps(pins,indent=2))
