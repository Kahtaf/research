from pathlib import Path
import ast,difflib,gzip,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];S=R/'source';B=S/'base';E=R/'evidence';P=R.parent/'2026-11-08-asus-pwrap-finite-backstop';checks={}
def check(n,v):
 assert v,n
 checks[n]=True
def body(s,name):
 a=re.search(r'\b'+re.escape(name)+r'\(',s).start();b=s.index('{',a);j=b+1;depth=1
 while depth:depth+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[b:j]
def txt(n):return (E/('linked-'+n+'.disasm')).read_text()
for n,v in json.loads((E/'prepost.json').read_text()).items():check('source_pins_'+n,hashlib.sha256((B/n).read_bytes()).hexdigest()==v['before'] and hashlib.sha256((S/n).read_bytes()).hexdigest()==v['after'])
old=(B/'drivers/power/supply/power_supply_sysfs.c').read_text();new=(S/'drivers/power/supply/power_supply_sysfs.c').read_text()
added='\tif (!strcmp(psy->desc->name, "battery")) {\n\t\tbattery_uevent_omitted();\n\t\treturn 0;\n\t}\n\n'
check('production_uevent_exact_original_except_omission',body(new,'power_supply_uevent').replace(added,'')==body(old,'power_supply_uevent'))
check('NAME_error_preserved_before_omission',body(new,'power_supply_uevent').index('if (ret)\n\t\treturn ret;')<body(new,'power_supply_uevent').index('battery_uevent_omitted()'))
old=(B/'drivers/power/supply/power_supply_core.c').read_text();new=(S/'drivers/power/supply/power_supply_core.c').read_text();w=body(new,'power_supply_changed_work')
for fragment in ['\tbool battery_uevent_armed;\n','\t\tbattery_uevent_armed = asus_battery_uevent_begin(psy);\n','\t\tasus_battery_uevent_publish(battery_uevent_armed, capture_ret);\n']:w=w.replace(fragment,'')
check('worker_entire_original_after_removing_only_record_plumbing',w==body(old,'power_supply_changed_work'))
check('sysfs_getter_and_thermal_functions_unchanged',body((B/'drivers/power/supply/power_supply_sysfs.c').read_text(),'power_supply_show_property')==body((S/'drivers/power/supply/power_supply_sysfs.c').read_text(),'power_supply_show_property') and body(old,'power_supply_read_temp')==body(new,'power_supply_read_temp'))
ret=(S/'arch/arm64/kernel/asus_retained_trace.c').read_text();oldret=(B/'arch/arm64/kernel/asus_retained_trace.c').read_text()
for n in ['asus_retained_trace_write','asus_devkmsg_boundary','trace_init','cap_init']:check('cold_trace_unchanged_'+n,body(ret,n)==body(oldret,n))
filter_add=' if (sparse_prefix(text, len, ASUS_BATTERY_UEVENT_PREFIX,\n                   sizeof(ASUS_BATTERY_UEVENT_PREFIX) - 1))\n  return true;\n'
check('only_narrow_fresh_prefix_admission',ret.replace(filter_add,'')==oldret)
ue=txt('power_supply_uevent');worker=txt('power_supply_changed_work');pub=txt('asus_battery_uevent_publish');begin=txt('asus_battery_uevent_begin')
check('ELF_actual_uevent_NAME_then_name_compare_then_omission',ue.index('<add_uevent_var>')<ue.index('<__pi_strcmp>') and ('<battery_uevent_omitted>' in ue or all(t in ue for t in ['ldxr','stlxr','stlr'])))
check('ELF_unmatched_original_getter_allocation_cleanup',all(x in ue for x in ['<get_zeroed_page>','<power_supply_show_property>','<kfree>','<free_pages>']))
check('ELF_worker_kobject_return_before_publisher',worker.index('<asus_battery_uevent_begin>')<worker.index('<kobject_uevent>')<worker.index('<asus_battery_uevent_publish>'))
# Native lock helpers bracket only original locked spans. Publisher is in the gap.
start=worker.index('<kobject_uevent>');end=worker.index('<asus_battery_uevent_publish>')
check('ELF_no_lock_between_call_return_and_publication',not re.search(r'<[^>]*(?:spin_lock|irq)[^>]*>',worker[start:end]))
check('ELF_context_and_single_claim_before_format',all(x in pub for x in ['daif','sp_el0','ldar','stlxr']) and pub.index('daif')<pub.index('<scnprintf>'))
check('ELF_publisher_only_formatter_direct_writer_stack_guard',set(re.findall(r'\bbl\s+[0-9a-f]+ <([^>]+)>',pub))=={'scnprintf','asus_retained_trace_write','__stack_chk_fail'})
check('ELF_record_has_no_clock_printk_allocation',not re.search(r'<[^>]*(?:clock|printk|kmalloc|regmap|pwrap)[^>]*>',pub+begin))
check('old_budget_drain_still_after_callback',txt('battery_get_property').index('<asus_p00a_battery_get_property>')<txt('battery_get_property').index('<asus_pwrap_backstop_publish>'))
p=json.loads((E/'packaging-receipt.json').read_text());build=json.loads((E/'build-receipt.json').read_text());i=json.loads((E/'identity.json').read_text())
check('single_build_no_helpers',build['kernel_builds']==1 and build['helper_compiles']==0)
check('frozen_components',all(v for k,v in p['preservation'].items() if k!='adapters'))
check('frozen_config',hashlib.sha256((R/'artifacts/resolved.config').read_bytes()).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1')
m=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());mp=json.loads((E/'System.map-uncompressed.json').read_text());check('genuine_System_map_pin',len(m)==mp['bytes'] and hashlib.sha256(m).hexdigest()==mp['sha256'])
check('source_inventory_before_single_build', (E/'CALLER-INVENTORY.md').exists() and len(json.loads((E/'caller-inventory-pins.json').read_text()))==6)
# Original installer execution classes/bodies remain exact.
def pyblock(s,n):
 a=next(x for x in ast.parse(s).body if getattr(x,'name',None)==n);return ''.join(s.splitlines(True)[a.lineno-1:a.end_lineno])
for n in ['execute','Transport','Guard']:check('installer_unchanged_'+n,pyblock((S/'install.py').read_text(),n)==pyblock((P/'source/install.py').read_text(),n))
check('adb_0755',((S/'adb').stat().st_mode&0o777)==0o755)
check('current_physical_preimage_admitted',p['base_full_p10']=='00f163a6a2500ec61b286be7bc6a3fa70f5bb707f2c554a217757649e1f4410e' and p['base_full_p10'] in (S/'install.py').read_text())
# Exact strict baseline decoder retained; additions only in this fork.
prior=(P/'scripts/decode_boundary.py').read_text();current=(R/'scripts/decode_boundary.py').read_text();(S/'decoder.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),current.splitlines(True),fromfile='frozen/decode_boundary.py',tofile='diagnostic/decode_boundary.py')))
for fragment in ["if not lines or lines[0]!=ENTRY:fail('fresh exact entry must be first console line')","if not text.endswith('\\n'):fail('truncated final line')","if any((ord(c)<32 and c!='\\n') or ord(c)>126 for c in text):fail('torn/non-ASCII-control console')","if active:fail('incomplete final write; missing boundary UNKNOWN')"]:check('baseline_decoder_rule_'+fragment[:35],fragment in current and fragment in prior)
spec=importlib.util.spec_from_file_location('omission_decoder',R/'scripts/decode_boundary.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
entry=d.ENTRY+'\n'+i['mode']+'\n';marker=d.BUEV+'SKIP first=2 before=1 after=2 same_task=1 uevent_rc=0\n'
rows=[('observe','actual','clock.path','CLOCK_MONOTONIC',d.CLOCK_PATH),('observe','begin','clock_gettime','loop.initial','-'),('observe','end','clock_gettime','loop.initial','0.642597153'),('observe','actual','sched.original','pid0','getparam_rc=0 getparam_errno=0 priority=0'),('observe','complete','runnable.loop','CLOCK_MONOTONIC','control='+i['control_uuid']+' iterations=2000000 checksum=e4ca7075 reason=compute-cap'),('after','complete','interrupts.snapshot','/proc/interrupts','synthetic-only')]
fixture=entry+marker
for seq,(phase,stage,op,path,value) in enumerate(rows,1):
 log=d.HELPER+f' phase={phase} stage={stage} op={op} path={path} rc=0 errno=0 value={value}';n=len(log)+4;fixture+=d.PREFIX+f'WENT seq={seq} len={n}\n'+log+'\n'+d.PREFIX+f'WRET seq={seq} len={n} rc={n}\n'
q=d.decode(fixture,p['full_p10']['sha256'],'SYNTHETIC_NOT_PHYSICAL','SYNTHETIC_NOT_PHYSICAL');check('synthetic_exact_record_and_separate_compute_afterIRQ',not q['errors'] and q['battery_uevent_omission']['status']=='OMISSION_AND_KOBJECT_RETURN_CAPTURED' and q['execution_facts']['compute_completion'] and q['execution_facts']['afterIRQ'] and q['execution_facts']['alarm_handler_count']==0)
cases={'missing':entry,'stale':entry+marker.replace(i['kernel_uuid'],'09abbded-4301-486b-8945-b8748248f2d2'),'correlation':entry+marker.replace('first=2','first=1'),'duplicate':entry+marker+marker,'range':entry+marker.replace('after=2','after=4294967296'),'stockproc-framing':'original stockproc preamble\n'+fixture}
for n,t in cases.items():
 q=d.decode(t);check('parser_'+n+'_UNKNOWN',q['battery_uevent_omission']['status']!='OMISSION_AND_KOBJECT_RETURN_CAPTURED' and (bool(q['errors']) if n!='missing' else not q['errors']))
(E/'synthetic-parser-fixture.txt').write_text('SYNTHETIC ONLY - never physical evidence\n'+fixture)
(E/'focused-checks.json').write_text(json.dumps(dict(status='PASS',checks=checks,synthetic_controls_not_physical=True),indent=2)+'\n');print('PASS focused source/ELF/frozen-package/parser checks:',len(checks))
