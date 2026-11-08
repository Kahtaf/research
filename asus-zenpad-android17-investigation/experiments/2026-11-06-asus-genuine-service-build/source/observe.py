"""One bounded read of the same native build handle; no restart or agent polling."""
from pathlib import Path
import datetime,importlib.util,json
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('service_build_remote',R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
CODE=r'''
from pathlib import Path
import datetime,json
R=Path('/srv/android/asus-genuine-service-build-r1')
pid=json.loads((R/'launch.json').read_text())['supervisor_pid']
p=Path('/proc')/str(pid)
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),supervisor_pid=pid,supervisor_live=p.exists(),supervisor_cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace') if p.exists() else None,native_engines=[])
for f in Path('/proc').iterdir():
 if not f.name.isdigit():continue
 try:comm=(f/'comm').read_text().strip();args=(f/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
 except OSError:continue
 if comm in ('siso','ninja','soong_ui','soong_build','ckati'):
  v['native_engines'].append(dict(pid=int(f.name),comm=comm,args=args[:250]))
for name in ['native-child.json','finished.json','supervisor-error.json']:
 v[name]=json.loads((R/name).read_text()) if (R/name).exists() else None
for name in ['native-build.log','supervisor.log']:
 f=R/name
 if f.exists():
  with f.open('rb') as h:h.seek(max(0,f.stat().st_size-4500));v[name]=h.read().decode(errors='replace')
print(json.dumps(v))
'''
result=json.loads(remote.run(CODE))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
with (R/'evidence'/('observation-'+stamp+'.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
