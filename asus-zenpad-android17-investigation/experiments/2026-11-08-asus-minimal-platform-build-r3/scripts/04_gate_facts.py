from pathlib import Path
import base64,hashlib,json,re
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');K=R/'kernel';files={};facts={}
for n in ['arch/Kconfig','kernel/trace/trace_sched_switch.c','drivers/base/Kconfig']:
 p=K/n
 if p.is_file():
  d=p.read_bytes();files['evidence/source-facts/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
  lines=d.decode().splitlines();hits=[]
  for i,l in enumerate(lines):
   if re.search('config SECCOMP_FILTER|config SECCOMP|select CONTEXT_SWITCH_TRACER|tracing_start_cmdline_record|initcall|register_trace_sched|register_tracer|sched_ref',l):hits.append(dict(line=i+1,text='\n'.join(lines[max(0,i-3):min(len(lines),i+9)])))
  facts[n]=hits
p=R/'out/.config';d=p.read_bytes();files['artifacts/resolution2.config']=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,facts=facts,resolved_sha256=hashlib.sha256(d).hexdigest())))
