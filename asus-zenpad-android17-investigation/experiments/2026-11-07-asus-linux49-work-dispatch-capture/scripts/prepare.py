from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-07-asus-linux49-active-work-capture'
sha=lambda b:hashlib.sha256(b).hexdigest()
i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid'];old_uuid='8e5c5d4d-6f94-4569-bfc6-63d92bac94a4'
names=['kernel/workqueue.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h']
# Exact public snapshots; remote source identity is confirmed before copying/build.
for n in names:
 p=B/'source'/n
 if not p.exists():p=B/'source/base'/n
 z=R/'source/base'/n;z.parent.mkdir(parents=True,exist_ok=True);z.write_bytes(p.read_bytes())
pins={};diff=[]
for n in names:
 old=(R/'source/base'/n).read_text();s=old
 if n=='kernel/workqueue.c':
  s=s.replace('#include <linux/export.h>','#include <linux/asus_retained_trace.h>\n#include <linux/export.h>',1)
  marker='\tstruct worker *collision;\n';assert s.count(marker)==1
  s=s.replace(marker,marker+'\tu64 dispatch_token;\n')
  marker='\tworker->current_func(work);';assert s.count(marker)==1
  hook='\tdispatch_token = asus_capture_work_enter(\n\t\t(unsigned long)READ_ONCE(worker->current_func), (unsigned long)work);\n'+marker+'\n\tasus_capture_work_return(dispatch_token);'
  s=s.replace(marker,hook);(R/'source/work-hook.inc').write_text(hook+'\n')
 elif n.endswith('asus_retained_trace.h'):
  s=s.replace('void asus_capture_switch(', 'u64 asus_capture_work_enter(unsigned long fn, unsigned long work);\nvoid asus_capture_work_return(u64 token);\nvoid asus_capture_switch(',1)
  s=s.replace('#else\n','#else\nstatic inline u64 asus_capture_work_enter(unsigned long fn, unsigned long work) { return 0; }\nstatic inline void asus_capture_work_return(u64 token) { }\n',1)
 elif n.endswith('asus_retained_trace.c'):
  s=s.replace(old_uuid,u)
  marker='static void __init cap_init(';assert s.count(marker)==1;s=s.replace(marker,(R/'source/work_capture.inc').read_text()+marker)
  s=s.replace(' BUILD_BUG_ON(SW_SIZE % 64);',' BUILD_BUG_ON(SW_SIZE % 64);\n BUILD_BUG_ON(WD_SIZE % 64);')
  # Only reservation/initialization/publication extend the existing cap_init.
  start=s.index('static void __init cap_init(');end=s.index('static bool cap_lock(',start)
  f=s[start:end].replace('CAP_SIZE + SW_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE')
  f=f.replace(' sw_init(dest + CAP_SIZE);',' sw_init(dest + CAP_SIZE);\n wd_init(dest + CAP_SIZE + SW_SIZE);')
  f=f.replace(' smp_store_release(&sw_area, dest + CAP_SIZE);',' smp_store_release(&sw_area, dest + CAP_SIZE);\n smp_store_release(&wd_area, dest + CAP_SIZE + SW_SIZE);')
  s=s[:start]+f+s[end:]
 elif n.endswith('asus_entry_tag.h'):
  s=s.replace(old_uuid,u).replace('82801d88bbccbd4b26ec4b89f20da448c0506d9956a5dd36a86d28636e0ee299',i['base_compiled_sha256'])
  i['tag']=s.split('"')[1].replace('\\n','\n');i['capture_tag']='A49CAP1 uuid='+u;i['config_sha256']='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
 assert s!=old
 p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=sha(old.encode()),after=sha(s.encode()))
 diff.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
p=json.loads((B/'evidence/preserved-source-pins.json').read_text());p.pop('kernel/workqueue.c');p['kernel/sched/core.c']=sha((B/'source/kernel/sched/core.c').read_bytes());(R/'evidence/preserved-source-pins.json').write_text(json.dumps(p,indent=2)+'\n')
# Keep old decoders byte-identical. Callers explicitly supply fresh UUID.
print(json.dumps(pins,indent=2))
