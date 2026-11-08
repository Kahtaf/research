from pathlib import Path
import base64,hashlib,json,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');K=R/'kernel';O=R/'out'
files={}
paths=['arch/arm64/lib/delay.c','arch/arm64/include/asm/delay.h','include/linux/delay.h','arch/arm64/include/asm/timex.h','arch/arm64/include/asm/arch_timer.h','include/clocksource/arm_arch_timer.h','kernel/panic.c','arch/arm64/kernel/asus_entry_tag.h']
for n in paths:
 p=K/n
 if not p.exists():continue
 d=p.read_bytes();files['source/ancestor/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
import re
facts={}
for key,pattern,paths in [('delay_calls',r'\b(__delay|__const_udelay|__udelay|__ndelay)\s*\(',[p for p in K.rglob('*') if p.suffix in ['.c','.h'] and ('arch' not in p.relative_to(K).parts or 'arm64' in p.relative_to(K).parts)]),('timer_rate',r'arch_timer_rate|arch_timer_read_counter|timer_set_delay|13000000',[K/'drivers/clocksource/arm_arch_timer.c',K/'arch/arm64/include/asm/timex.h',K/'include/clocksource/arm_arch_timer.h'])]:
 rows=[]
 for p in paths:
  for i,l in enumerate(p.read_text(errors='replace').splitlines()):
   if re.search(pattern,l):rows.append(dict(path=str(p.relative_to(K)),line=i+1,text=l))
 facts[key]=rows
facts['linked_pins']={n:dict(bytes=(O/n).stat().st_size,sha256=hashlib.sha256((O/n).read_bytes()).hexdigest()) for n in ['arch/arm64/boot/Image.gz-dtb','System.map','.config']}
# Fetch only public source, never device/private payloads.
print(json.dumps(dict(files=files,facts=facts)))
