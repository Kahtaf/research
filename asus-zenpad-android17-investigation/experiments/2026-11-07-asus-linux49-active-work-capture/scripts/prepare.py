from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid']
oldcall='\tasus_capture_switch(prev, prev_state);'
newcall='''#ifdef CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE
	{
		struct worker *worker;
		unsigned long active_func = 0, active_work = 0;
		unsigned int worker_flags = 0;

		/* Own current worker only, at the original locked switch seam. */
		if (nr_cpu_ids == 1 && !raw_smp_processor_id() &&
		    irqs_disabled() && in_task()) {
			worker_flags = !!(READ_ONCE(current->flags) & PF_WQ_WORKER);
			worker = current_wq_worker();
			if (worker) {
				worker_flags |= 2;
				active_func = (unsigned long)READ_ONCE(worker->current_func);
				active_work = (unsigned long)READ_ONCE(worker->current_work);
			}
		}
		asus_capture_switch(prev, prev_state, active_func, active_work,
				    worker_flags);
	}
#endif'''
names=['kernel/sched/core.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h'];pins={};diff=[]
for n in names:
 old=(R/'source/base'/n).read_text();s=old
 if n=='kernel/sched/core.c':
  assert s.count(oldcall)==1;s=s.replace(oldcall,newcall)
 elif n.endswith('asus_retained_trace.h'):
  s=s.replace('struct task_struct *prev, long prev_state)','struct task_struct *prev, long prev_state,\n                         unsigned long active_func, unsigned long active_work,\n                         unsigned int worker_flags)')
 elif n.endswith('asus_retained_trace.c'):
  s=s.replace('SW_ROW_SIZE 256','SW_ROW_SIZE 320').replace('SW_SIZE != 3008','SW_SIZE != 3648').replace('A49SW1','A49SW2').replace('3d26cc95-11a8-41a2-ac62-3a2a33bd506e',u)
  s=s.replace('j < 11','j < 14').replace('line + 196','line + 248').replace('line + 232','line + 288').replace("line[255]",'line[SW_ROW_SIZE - 1]')
  s=s.replace('struct task_struct *prev, long prev_state)','struct task_struct *prev, long prev_state,\n                         unsigned long active_func, unsigned long active_work,\n                         unsigned int worker_flags)').replace('u64 f[11], raw;','u64 f[14], raw;')
  s=s.replace(' f[10] = READ_ONCE(cap_serial);',' f[10] = READ_ONCE(cap_serial);\n f[11] = active_func;\n f[12] = active_work;\n f[13] = worker_flags;')
 elif n.endswith('asus_entry_tag.h'):
  s=s.replace('3d26cc95-11a8-41a2-ac62-3a2a33bd506e',u).replace('804ad2c23885e1603ac7c3871fbb0bc9a793521ea106ad7d0f95331a6d5ef55e',i['base_compiled_sha256'])
 assert s!=old
 p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=sha(old.encode()),after=sha(s.encode()))
 diff.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();(R/'source/switch_capture.inc').write_text(s[s.index('/* Independent scheduler capture:'):s.index('static void __init cap_init(')])
preserved=json.loads((R/'evidence/preserved-source-pins.json').read_text())
for n in ['kernel/workqueue_internal.h','kernel/workqueue.c','kernel/kthread.c','include/linux/kthread.h','include/linux/sched.h','arch/arm64/include/asm/current.h','arch/arm64/kernel/asm-offsets.c','arch/arm64/include/asm/arch_timer.h','arch/arm64/mm/cache.S']:preserved[n]=sha((R/'source/base'/n).read_bytes())
(R/'evidence/preserved-source-pins.json').write_text(json.dumps(preserved,indent=2)+'\n')
(R/'source/core-hook.inc').write_text(newcall+'\n')
print(json.dumps(pins,indent=2))
