from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
p=Path(sys.argv[1]);script=p.read_text();name=p.stem+('-'+'-'.join(sys.argv[2:]) if len(sys.argv)>2 else '')
remote_script=f'''from pathlib import Path
import subprocess,os,json
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106')
p=O/'source'/{p.name!r}
if p.exists():assert p.read_text()=={script!r}
else:p.write_text({script!r})
log=(O/'evidence'/{(name+'.supervisor.log')!r}).open('w')
job=subprocess.Popen(['python3','-B',str(p),*{sys.argv[2:]!r}],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
(O/'evidence'/{(name+'.pid')!r}).write_text(str(job.pid)+'\\n')
print(json.dumps({{'pid':job.pid,'script':str(p)}}))
'''
out=remote.run(remote_script);(ROOT/'evidence'/(name+'.launch.json')).write_text(out);print(out)
