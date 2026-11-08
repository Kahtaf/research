"""Direct affected-object compiles using the completed e9 command receipts.

No make invocation; original source and out trees are read-only inputs.
All compiler outputs/dependencies and the header overlay go to a fresh spike.
"""
from pathlib import Path
import importlib.util, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1]; W=R.parent
spec=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
files={str(p.relative_to(R/'patched')):p.read_text() for p in (R/'patched').rglob('*') if p.is_file()}
cmds={n:(R/'evidence'/('.'+n+'.o.cmd')).read_text().splitlines()[0].split(' := ',1)[1] for n in ('setup','printk','main')}
script='''from pathlib import Path
import hashlib,json,shlex,subprocess,time
r=Path('/srv/android/asus-linux49-retained-boot-trace-20261107')
k=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
out=k.parent/'out'
assert not r.exists(), 'Isolated compile destination already exists; do not overwrite it'
r.mkdir()
files=FILES
cmds=CMDS
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original={f:sha(k/f) for f in files if (k/f).is_file()}
original['../out/.config']=sha(out/'.config')
for f,t in files.items():
 p=r/'patched'/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
results=[]
for name,source,template in [('asus_retained_trace','arch/arm64/kernel/asus_retained_trace.c','setup'),('setup','arch/arm64/kernel/setup.c','setup'),('printk','kernel/printk/printk.c','printk'),('main','init/main.c','main')]:
 args=shlex.split(cmds[template]); oi=args.index('-o')
 args[oi+1]=str(r/(name+'.o'));args[-1]=str(r/'patched'/source)
 args=[('-Wp,-MD,'+str(r/(name+'.d'))) if x.startswith('-Wp,-MD,') else x for x in args]
 args[1:1]=['-I'+str(r/'patched/include'),'-DCONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=1']
 start=time.monotonic()
 p=subprocess.run(args,cwd=out,text=True,capture_output=True,timeout=90)
 item={'name':name,'source':source,'argv':args,'exit':p.returncode,'seconds':round(time.monotonic()-start,3),'stdout':p.stdout,'stderr':p.stderr}
 if p.returncode==0:item['sha256']=sha(r/(name+'.o'));item['bytes']=(r/(name+'.o')).stat().st_size
 results.append(item)
 if p.returncode:break
preserved={f:sha(k/f)==h for f,h in original.items()}
report={'remote_spike':str(r),'config_sha256':original['../out/.config'],'results':results,'original_inputs_preserved':preserved}
(r/'compile.json').write_text(json.dumps(report,indent=2)+'\\n')
print(json.dumps(report))
'''.replace('FILES',repr(files)).replace('CMDS',repr(cmds))
result=json.loads(remote.run(script))
(R/'evidence/compile.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'objects':[{k:v[k] for k in ('name','exit','stderr','seconds')} for v in result['results']], 'preserved':result['original_inputs_preserved']},indent=2))
