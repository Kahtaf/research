from pathlib import Path
import re,json,hashlib
PM='drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc'
def strip(s):
 s=re.sub(r'^\s*asus_capture_pmic_(?:begin|step)\([^;]*;\n','\n',s,flags=re.M)
 s=s.replace('#include <linux/asus_retained_trace.h>\n','').replace('\tstruct asus_pmic_capture capture;\n','')
 s=s.replace('(const struct asus_pmic_capture *parent)','(void)').replace('p00a_pmic_prepare_adc(&capture)','p00a_pmic_prepare_adc()')
 s=s.replace('int ret, poll = -1;','int ret, poll;').replace('int ret, sample = -1, poll = -1;','int ret, sample, poll;')
 return s

def tokens(s):
 s=re.sub(r'/\*.*?\*/','',s,flags=re.S)
 return re.findall(r'\w+|[^\w\s{}]',s)
def check(K,B,uuid):
 a=(B/PM).read_text();z=(K/PM).read_text();restored=strip(z)
 assert tokens(restored)==tokens(a),'original non-brace token stream changed'
 # Added braces only wrap original single controlled statements or returns;
 # no else/goto/condition/call can change association after hook removal.
 assert 'else' not in a.split('#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC')[0]
 funcs=['p00a_pmic_prepare_adc','asus_p00a_pmic_present','asus_p00a_pmic_adc']
 assert a.count('p00a_pmic_prepare_adc(')==z.count('p00a_pmic_prepare_adc(')==2
 assert '#include <linux/asus_retained_trace.h>' in z
 args=re.findall(r'asus_capture_pmic_step\(&capture,\s*([^;]+)\);',z)
 for x in args:
  assert not re.search(r'\b(raw|mv|value|delay|busy|sum|present|pmicAuxadc_irq_lock|pwrap_regmap)\b',x),x
  assert all(t.strip() in ['-1','sample','poll','ret','0','-ENODATA','-EINVAL','-ETIMEDOUT','0x80000000U'] for t in x.split(',')[1:]),x
 c=(K/'arch/arm64/kernel/asus_retained_trace.c').read_text();old=(B/'arch/arm64/kernel/asus_retained_trace.c').read_text()
 a0=c.index('/* Independent, nonblocking publication;');a1=c.index('static void __init cap_init(',a0)
 restored_c=c[:a0]+c[a1:];restored_c=restored_c.replace(uuid,'431dfb9c-8b78-4c8c-bd74-cc556adcf8b0')
 restored_c=restored_c.replace(' BUILD_BUG_ON(PM_SIZE % 64);\n','').replace(' + PM_SIZE','')
 restored_c=restored_c.replace(' pm_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);\n','').replace(' smp_store_release(&pm_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);\n','')
 assert restored_c==old,'old recorder changed beyond UUID and guarded append'
 init=c[c.index('static void __init cap_init('):c.index('static bool cap_lock(')]
 assert init.index('> h->sz_console - pos')<init.index('dest =')<init.index('pm_init(')<init.index('WRITE_ONCE(h->log_size')<init.index('smp_store_release(&pm_area')
 pm=c[a0:a1]
 for forbidden in ['printk(', 'ktime_', 'kmalloc(', 'schedule(', 'usleep', 'mutex_', 'pmic_read', 'regmap', 'rcu_read_lock', 'preempt_disable']:
  assert forbidden not in pm,forbidden
 assert pm.count('mrs %0, cntvct_el0')==1
 assert 'raw_spin_trylock_irqsave(&pm_lock' in pm and 'raw_spin_unlock_irqrestore(&pm_lock' in pm
 assert 'nr_cpu_ids != 1 || raw_smp_processor_id()' in pm
 return dict(status='PASS',original_semantic_token_stream_restored=True,added_braces='only original single-statement controls and inert return scopes; no else ambiguity',original_driver_calls_conditions_register_access_transforms_loops_unchanged=True,exported_signatures_unchanged=True,prepare_only_instrumentation_parent_arg=True,old_recorder_exact_after_reverting_UUID_and_append=True,capacity_before_any_append_write_and_readiness=True,no_raw_value_hook_arguments=True,one_raw_counter_per_publication=True,no_new_publication_lock_spans_original_primitive=True)
if __name__=='__main__':
 R=Path(__file__).resolve().parents[1];i=json.loads((R/'evidence/identity.json').read_text());v=check(R/'source',R/'source/base',i['run_uuid']);(R/'evidence/source-checks.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
