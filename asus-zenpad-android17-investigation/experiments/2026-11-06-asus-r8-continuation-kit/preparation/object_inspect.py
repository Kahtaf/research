exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import os,resource,subprocess,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/wpa-r2');tool=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-dis')
p=subprocess.run([str(tool),str(F/'candidate.o'),'-o',str(F/'candidate.ll')],capture_output=True,text=True);assert p.returncode==0,p.stderr
s=(F/'candidate.ll').read_text();print(json.dumps(dict(exit=0,target=[l for l in s.splitlines() if l.startswith('target ')],functions=[l.split('(')[0] for l in s.splitlines() if l.startswith('define ')],native_product_object=False),indent=2))
''');Path('2026-11-06-asus-r8-continuation-kit/evidence/wpa-object-inspection.json').write_text(r);print(r)
