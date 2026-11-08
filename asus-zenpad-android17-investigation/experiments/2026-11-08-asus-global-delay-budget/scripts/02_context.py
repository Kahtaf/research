from pathlib import Path
import base64,hashlib,json,re,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');K=R/'kernel';O=R/'out';files={}
paths=['include/asm-generic/delay.h','include/asm-generic/timex.h','init/calibrate.c','drivers/clocksource/arm_arch_timer.c','arch/arm64/kernel/time.c','arch/arm64/include/asm/processor.h','arch/arm64/Makefile','arch/arm64/kernel/setup.c','drivers/misc/mediatek/mtprof/prof_main.c']
for n in paths:
 p=K/n;d=p.read_bytes();files['source/ancestor/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
q=subprocess.check_output(['aarch64-linux-gnu-objdump','-d',str(O/'vmlinux')],text=True)
lines=q.splitlines();hits=[];func=''
for i,l in enumerate(lines):
 if re.match(r'[0-9a-f]+ <[^>]+>:',l):func=l
 if re.search(r'\b(?:bl|b)\s+[0-9a-f]+ <__(?:delay|const_udelay|udelay|ndelay)>',l):hits.append(dict(function=func,text='\n'.join(lines[max(0,i-10):i+3])))
# Retained mediatek/panic/reset calls: collect only unusually large literal requests and variables, bounded source context.
scopes=[K/'drivers/misc/mediatek',K/'kernel/panic.c',K/'arch/arm64']
rows=[]
for scope in scopes:
 ps=[scope] if scope.is_file() else [p for p in scope.rglob('*') if p.suffix in ['.c','.h']]
 for p in ps:
  ls=p.read_text(errors='replace').splitlines()
  for i,l in enumerate(ls):
   m=re.search(r'\b(udelay|ndelay|mdelay)\s*\(([^()]*)\)',l)
   if m and (not m[2].strip().isdigit() or int(m[2].strip())>5000):rows.append(dict(path=str(p.relative_to(K)),line=i+1,text='\n'.join(ls[max(0,i-3):i+4])))
print(json.dumps(dict(files=files,linked_delay_calls=hits,unusually_large_or_variable_delay_context=rows,config={l.split('=')[0]:l.split('=',1)[1] for l in (O/'.config').read_text().splitlines() if l.startswith(('CONFIG_HZ=','CONFIG_GENERIC_CALIBRATE_DELAY=','CONFIG_PANIC_TIMEOUT=','CONFIG_DEBUG_BUGVERBOSE='))})))
