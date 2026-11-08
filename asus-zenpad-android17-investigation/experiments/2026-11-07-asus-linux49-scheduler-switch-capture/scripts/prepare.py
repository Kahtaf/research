from pathlib import Path
import json,hashlib,difflib,re
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
names=['kernel/sched/core.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h']
inc=(R/'source/switch_capture.inc').read_text().replace('sw_fault(33)','sw_fault(36)').replace('sw_fault(22)','sw_fault(24)').replace('sw_fault(44)','sw_fault(47)').replace('overflow=0", 44','overflow=0", 48')
for key,label in [('a','BEGIN'),('z','END  ')]:
 text='A49SGUARD '+label+' 3d26cc95-11a8-41a2-ac62-3a2a33bd506e';text=text.ljust(63)+'\n';assert len(text)==64
 inc=re.sub(r'static const char sw_guard_'+key+r'\[\] = .*?;',lambda m:'static const char sw_guard_'+key+'[] = '+json.dumps(text)+';',inc)
(R/'source/switch_capture.inc').write_text(inc)
pins={};diff=[]
for n in names:
 old=(R/'source/base'/n).read_text();s=old
 if n=='kernel/sched/core.c':
  s=s.replace('#include <linux/kasan.h>','#include <linux/kasan.h>\n#include <linux/asus_retained_trace.h>')
  assert s.count('\tprev_state = prev->state;')==1
  s=s.replace('\tprev_state = prev->state;','\tprev_state = prev->state;\n\tasus_capture_switch(prev, prev_state);')
 elif n.endswith('asus_retained_trace.h'):
  s=s.replace('#ifdef CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE','struct task_struct;\n#ifdef CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE\nvoid asus_capture_switch(struct task_struct *prev, long prev_state);')
  s=s.replace('#else\n','#else\nstatic inline void asus_capture_switch(struct task_struct *prev, long prev_state) { }\n',1)
 elif n.endswith('asus_retained_trace.c'):
  s=s.replace('static void __init cap_init(struct trace_header *h)',inc+'\nstatic void __init cap_init(struct trace_header *h)')
  s=s.replace('BUILD_BUG_ON(CAP_SIZE % 64);','BUILD_BUG_ON(CAP_SIZE % 64);\n BUILD_BUG_ON(SW_SIZE % 64);')
  s=s.replace('CAP_SIZE > h->sz_console - pos','CAP_SIZE + SW_SIZE > h->sz_console - pos')
  s=s.replace(' __clean_dcache_area_poc((char *)h + h->off_console + h->log_size,\n                         pos + CAP_SIZE - h->log_size);',' sw_init(dest + CAP_SIZE);\n __clean_dcache_area_poc((char *)h + h->off_console + h->log_size,\n                         pos + CAP_SIZE + SW_SIZE - h->log_size);')
  s=s.replace('WRITE_ONCE(h->log_size, pos + CAP_SIZE);','WRITE_ONCE(h->log_size, pos + CAP_SIZE + SW_SIZE);')
  s=s.replace('smp_store_release(&cap_area, dest);','smp_store_release(&cap_area, dest);\n smp_store_release(&sw_area, dest + CAP_SIZE);')
 elif n.endswith('asus_entry_tag.h'):
  i=json.loads((R/'evidence/identity.json').read_text());s=s.replace('d140b2bf-e06f-4ba7-8203-83a1c4ce4119',i['run_uuid']).replace('1baa4bd8ea91477eb0592bc51d2d25a4cab8afe94c3c0014f98e2d4b222fbd90',i['base_compiled_sha256'])
 assert s!=old
 p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=sha(old.encode()),after=sha(s.encode()))
 diff.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(pins,indent=2))
