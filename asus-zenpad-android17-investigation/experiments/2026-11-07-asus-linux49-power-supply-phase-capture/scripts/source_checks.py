from pathlib import Path
import re,hashlib,json
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def function(s,n):
 a=s.index(n+'(');a=s.index('{',a);depth=1;i=a+1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def check(K,B,uuid):
 old=(B/'drivers/power/supply/power_supply_core.c').read_text();new=(K/'drivers/power/supply/power_supply_core.c').read_text()
 restored=new.replace('#include <linux/asus_retained_trace.h>\n','',1)
 restored=re.sub(r'\n[ \t]*asus_capture_ps_(?:begin|step)\([^;]*;', '',restored)
 restored=restored.replace('\tstruct asus_ps_capture capture;\n','').replace('\tint capture_ret;\n','')
 restored=restored.replace('\t\tif (pst->desc->external_power_changed) {\n\t\t\tpst->desc->external_power_changed(pst);\n\t\t}', '\t\tif (pst->desc->external_power_changed)\n\t\t\tpst->desc->external_power_changed(pst);',1)
 restored=restored.replace('\t} else {\n\t}', '\t}',1)
 restored=restored.replace('\tif (likely(!psy->changed)) {\n\t\tpm_relax(&psy->dev);\n\t}', '\tif (likely(!psy->changed))\n\t\tpm_relax(&psy->dev);',1)
 restored=restored.replace('capture_ret = class_for_each_device(', 'class_for_each_device(',1).replace('capture_ret = atomic_notifier_call_chain(', 'atomic_notifier_call_chain(',1).replace('capture_ret = kobject_uevent(', 'kobject_uevent(',1)
 restored=restored.replace('{\n\n\tif (atomic_read(&psy->use_cnt) <= 0)', '{\n\tif (atomic_read(&psy->use_cnt) <= 0)',1)
 restored=restored.replace('capture_ret = psy->desc->get_property(psy, psp, val);\n\treturn capture_ret;', 'return psy->desc->get_property(psy, psp, val);',1)
 assert restored==old,'core.c exact reverse-transform preservation'
 f=function(new,'__power_supply_changed_work');assert f.count('__power_supply_is_supplied_by(psy, pst)')==1 and f.count('pst->desc->external_power_changed(pst);')==1
 assert f.index('__power_supply_is_supplied_by(')<f.index('if (pst->desc->external_power_changed)')<f.index('asus_capture_ps_begin(')<f.index('pst->desc->external_power_changed(pst);')<f.index('asus_capture_ps_step(')
 f=function(new,'power_supply_get_property')
 assert f.count('psy->desc->get_property(psy, psp, val);')==1 and f.index('return -EAGAIN')<f.index('return -ENODEV')<f.index('asus_capture_ps_begin(')<f.index('capture_ret = psy->desc->get_property')<f.index('asus_capture_ps_step(')<f.index('return capture_ret')
 tail=f[f.index('asus_capture_ps_step('):];assert 'psy->' not in tail and '*val' not in tail
 oldrec=(B/'arch/arm64/kernel/asus_retained_trace.c').read_text();rec=(K/'arch/arm64/kernel/asus_retained_trace.c').read_text();prev='b4702f9a-6b32-423f-b789-d2bd515c0707'
 oldfuncs=['cap_hex','cap_fault','cap_publish','cap_lock','cap_enter','cap_match','asus_capture_mono_enter','asus_capture_mono_seq','asus_capture_exit','asus_capture_counter_enter','asus_capture_event_enter','trace_overlaps','trace_check_dt','asus_retained_trace_write','trace_init','sw_commit','sw_fault','sw_header','sw_init','asus_capture_switch','wd_fault','wd_header','wd_init','wd_record','asus_capture_work_enter','asus_capture_work_return']
 for n in oldfuncs:assert function(oldrec,n).replace(prev,uuid)==function(rec,n),n
 f=function(rec,'cap_init')
 restored=f.replace(' BUILD_BUG_ON(PS_SIZE % 64);\n','').replace('CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE').replace(' ps_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE);\n','').replace(' smp_store_release(&ps_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE);\n','')
 assert restored==function(oldrec,'cap_init'),'only reservation/append/readiness extension'
 assert f.index('PS_SIZE > h->sz_console - pos')<f.index('memset(')<f.index('ps_init(')<f.index('WRITE_ONCE(h->log_size')<f.index('smp_store_release(&ps_area')
 assert 'strnlen(name, 16);' in function(rec,'ps_name') and 'memcpy(dest, name, len);' in function(rec,'ps_name')
 p=function(rec,'ps_record');assert p.count('raw_spin_trylock_irqsave')==1 and p.count('raw_spin_unlock_irqrestore')==1 and p.count('cntvct_el0')==1
 assert not re.search(r'\b(?:printk|ktime\w*|kmalloc|kzalloc|schedule|msleep|mutex_lock|spin_lock\w*|raw_spin_lock\w*)\s*\(',p)
 assert 'pc !=' not in p and 'pc >' not in p and '!in_task()' not in p and 'in_nmi()' in p
 return dict(status='PASS_EXACT_SOURCE_REVERSE_TRANSFORM',core_entire_file_restores_byte_exact=True,old_capture_bodies_unchanged_except_UUID=oldfuncs,property_early_returns_and_single_original_call=True,external_supplied_by_once_and_original_callback_once=True,postcall_uses_local_snapshot_only=True,capacity_before_any_write_and_readiness=True,bounded_names=True,one_nonblocking_independent_lock=True,nonzero_atomic_context_admitted=True)
if __name__=='__main__':
 R=Path(__file__).resolve().parents[1];i=json.loads((R/'evidence/identity.json').read_text());print(json.dumps(check(R/'source',R/'source/base',i['run_uuid']),indent=2))
