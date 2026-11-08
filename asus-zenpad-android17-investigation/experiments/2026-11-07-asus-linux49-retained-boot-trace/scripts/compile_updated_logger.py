"""Recompile only the logger after its final publication-order refinement."""
from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
spec=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prior=json.loads((R/'evidence/compile.json').read_text())
source=(R/'patched/arch/arm64/kernel/asus_retained_trace.c').read_text()
script='''from pathlib import Path
import hashlib,json,subprocess,time
r=Path('/srv/android/asus-linux49-retained-boot-trace-20261107')
k=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
args=ARGS
p=r/'patched/arch/arm64/kernel/asus_retained_trace.c'
p.write_text(SOURCE)
start=time.monotonic()
c=subprocess.run(args,cwd=k.parent/'out',capture_output=True,text=True,timeout=90)
result={'exit':c.returncode,'seconds':round(time.monotonic()-start,3),'stderr':c.stderr,'stdout':c.stdout,
 'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256((r/'asus_retained_trace.o').read_bytes()).hexdigest(),
 'original_inputs_preserved':{f:hashlib.sha256((k/f).read_bytes()).hexdigest()==h for f,h in ORIGINAL.items()}}
(r/'final-logger-compile.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
'''.replace('ARGS',repr(prior['results'][0]['argv'])).replace('SOURCE',repr(source))
original={f:receipt['sha256'] for f,receipt in json.loads((R/'evidence/source-receipts.json').read_text()).items() if f in ('arch/arm64/kernel/setup.c','arch/arm64/kernel/Makefile','arch/arm64/Kconfig.debug','kernel/printk/printk.c')}
original['../out/.config']=prior['config_sha256']
script=script.replace('ORIGINAL',repr(original))
d=json.loads(m.run(script));(R/'evidence/final-logger-compile.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
