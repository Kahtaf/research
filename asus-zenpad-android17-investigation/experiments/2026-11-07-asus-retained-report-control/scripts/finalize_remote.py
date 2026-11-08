from pathlib import Path
import importlib.util,base64,json
R=Path(__file__).resolve().parents[1];W=R.parent
spec=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rels=['artifacts/candidate.img','artifacts/candidate.p10.raw','source/early-retained-checkpoint.patch','source/trace-after/arch/arm64/kernel/asus_retained_trace.c','source/trace-after/arch/arm64/kernel/setup.c','source/trace-after/include/linux/asus_retained_trace.h','evidence/packaging-receipt.json','evidence/install-plan.json','evidence/next-trace-patch.json']
payload={p:base64.b64encode((R/p).read_bytes()).decode() for p in rels}
out=m.run(f'''from pathlib import Path
import base64,subprocess,json,hashlib
R=Path('/srv/android/asus-retained-report-control-20261107')
for p,data in {payload!r}.items():
 d=R/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(base64.b64decode(data))
refs={{}}
K=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
for p in ['include/asm-generic/fixmap.h','arch/arm64/include/asm/pgtable-prot.h','arch/arm64/mm/ioremap.c','arch/arm64/mm/init.c']:
 data=(K/p).read_bytes();dest=R/'source/kernel-reference'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);refs[p]=base64.b64encode(data).decode()
checks={{}}
for name,cmd in [('static-elf',['aarch64-linux-gnu-readelf','-h','-l',str(R/'artifacts/init')]),('retained-helper',['aarch64-linux-gnu-objdump','-d','--disassemble=retained_marker',str(R/'artifacts/init')])]:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);assert p.returncode==0;checks[name]=p.stdout
# Record actual readbacks from the owned delivery, not a claimed transfer alone.
pins={{p:dict(bytes=(R/p).stat().st_size,sha256=hashlib.sha256((R/p).read_bytes()).hexdigest()) for p in {rels!r}}}
print(json.dumps(dict(refs=refs,checks=checks,pins=pins)))
''')
a=json.loads(out)
for p,data in a['refs'].items():
 dest=R/'source/kernel-reference'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(base64.b64decode(data))
for name,txt in a['checks'].items():(R/'evidence'/(name+'.txt')).write_text(txt)
(R/'evidence/remote-delivery.json').write_text(json.dumps(a['pins'],indent=2)+'\n')
print(json.dumps(a['pins'],indent=2))
