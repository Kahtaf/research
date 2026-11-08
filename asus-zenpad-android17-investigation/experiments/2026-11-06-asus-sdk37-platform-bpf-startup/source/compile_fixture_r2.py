from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('builder_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
source=(ROOT/'source/fixture_init_r2.c').read_text()
script=f'''from pathlib import Path
import os,subprocess as s,json,hashlib
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');os.sched_setaffinity(0,{{min(os.sched_getaffinity(0))}})
p=O/'source/fixture_init_r2.c';assert not p.exists();p.write_text({source!r})
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(p),'-o',str(O/'artifacts/fixture-init-r2')]
q=s.run(cmd,capture_output=True,text=True);(O/'evidence/fixture-compile-r2.log').write_text(q.stdout+q.stderr)
record={{'argv':cmd,'exit':q.returncode,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cpu_affinity':list(os.sched_getaffinity(0))}}
if q.returncode==0:record['elf_sha256']=hashlib.sha256((O/'artifacts/fixture-init-r2').read_bytes()).hexdigest()
(O/'evidence/fixture-compile-r2.json').write_text(json.dumps(record,indent=2)+'\\n');print(json.dumps(record));print(q.stdout+q.stderr)
'''
out=m.run(script);(ROOT/'evidence/compile_fixture_r2.txt').write_text(out);print(out)
