from pathlib import Path
import base64,hashlib,json,re,subprocess
B=Path('/srv/android/asus-minimal-platform-build-r2-20261108');K=B/'kernel';O=B/'out';files={};facts={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['kernel/trace/Kconfig','kernel/trace/Makefile','kernel/trace/trace.c','kernel/trace/trace_nop.c','kernel/trace/trace_events.c','drivers/misc/mediatek/thermal/virtual_sensor_cooler_backlight.c','drivers/misc/mediatek/thermal/Makefile','drivers/misc/mediatek/thermal/Kconfig','drivers/misc/mediatek/met_drv/Kconfig','drivers/misc/mediatek/met_drv/Makefile']
for n in paths:
 p=K/n
 if p.is_file():d=p.read_bytes();files['evidence/source-facts/'+n]=dict(data=base64.b64encode(d).decode(),sha256=sha(p))
# Small directory-scoped scans of trace initialization and the retained MET wrapper/init, never the whole kernel.
scopes={'trace':[p for p in (K/'kernel/trace').glob('*.c')], 'MET':[p for p in (K/'drivers/misc/mediatek/met_drv').rglob('*') if p.is_file() and (p.suffix in ['.c','.h'] or p.name.startswith('Kconfig'))], 'init':[K/'init/main.c']}
patterns={'trace':r'MTK.*(?:FTRACE|TRAC)|ftrace.*default|tracing_on\(|tracing_start\(|trace_set_clr_event\(|tracing_set_tracer\(|trace_buf_size\s*=|tracing_disabled\s*=|tracer_tracing_on\(|bootup_tracer|boot.*trace|TRACE_BUF_SIZE_DEFAULT|TRACE_BUF_SIZE_MIN|RING_BUFFER_[A-Z_]+', 'MET':r'met_tracing_record_cmdline|tracing_record_cmdline|module_init|_initcall\(|met_run\s*=|metmode\s*=|mode\s*=|ftrace.*enable|tracing_on\(|tracing_start\(|trace_set_clr_event\(|tracing_set_tracer\(|DEFAULT_ENABLE|trace_buf_size|buffer_size|[A-Za-z_]*start[A-Za-z_]*\(', 'init':r'trac|met_'}
for key,ps in scopes.items():
 hits=[]
 for p in ps:
  lines=p.read_text(errors='replace').splitlines()
  for i,l in enumerate(lines):
   if re.search(patterns[key],l,re.I if key=='MET' else 0):hits.append(dict(path=str(p.relative_to(K)),line=i+1,text='\n'.join(lines[max(0,i-2):min(len(lines),i+4)])))
 facts[key]=dict(files_scanned=len(ps),hits=hits)
# Bind the actual unconditional MET wrapper and init implementation, if selected by scoped matches.
for x in facts['MET']['hits']:
 if 'met_tracing_record_cmdline' in x['text'] or 'module_init' in x['text']:
  p=K/x['path'];n='evidence/source-facts/'+x['path'];d=p.read_bytes();files[n]=dict(data=base64.b64encode(d).decode(),sha256=sha(p))
# Existing r2 relocation records, no compilation.
for name in ['met_tracing_record_cmdline','virtual_sensor_set_cur_state','battery_meter_dts_probe','battery_meter_dts_remove']:
 d=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr','--disassemble='+name,str(O/'drivers/built-in.o')],text=True).encode();files['evidence/existing-'+name+'.disasm']=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,scope_facts=facts,source_config_sha256=sha(O/'.config'))))
