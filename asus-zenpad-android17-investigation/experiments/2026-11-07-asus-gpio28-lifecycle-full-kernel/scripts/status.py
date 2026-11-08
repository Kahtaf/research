from transport import run,L,R
import json
s='''from pathlib import Path
import json
R=Path(PREFIX)
s=json.loads((R/'evidence/build-status.json').read_text())
s['observed_utc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
log=R/'evidence/Image.gz-dtb.log'
if log.exists():
 with log.open('rb') as f:
  f.seek(max(0,log.stat().st_size-4096));s['last_build_output']=f.read().decode(errors='replace').splitlines()[-4:]
print(json.dumps(s,indent=2))
'''.replace('PREFIX',repr(R))
r=run(s);(L/'evidence/build-status.json').write_text(r);s=json.loads(r);print(json.dumps({'status':s['status'],'started':s['started'],'observed_utc':s.get('observed_utc'),'last_build_output':s.get('last_build_output'),'stages':[{'targets':c['command'][10:],'exit':c.get('exit'),'finished':c.get('finished')} for c in s['commands']],'owned_output_allocated_bytes':s.get('owned_output_allocated_bytes'),'error':s.get('error'),'finished':s.get('finished')},indent=2))
