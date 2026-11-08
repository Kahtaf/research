from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent));from remote_owned import run
L=Path(__file__).resolve().parents[1]
names=['evidence/'+n for n in ['elf-binding.json','focused-replay.json','leaf-identity.json','leaf-build.json','leaf-abi.json','leaf-binary-binding.json','kernel-selection.json','reference-sources.json','admission.json','boot-ramdisk-corroboration.json','cow-verification.json','adaptations.json','startup-pipeline-initial-result.json','cow-verifier-resume.txt']]
names+=['source/'+n for n in ['Loader.pre.cpp','Loader.cpp','loader-prog-name.patch','patcher.c','cow.py','cow-before-extent1.py','observer.c']]
names+=['attempt-compile-floor/'+n for n in ['Loader.cpp','loader-prog-name.patch','leaf-build.json','leaf-identity.json']]
names+=['run-trace/result.json','run-candidate/result.json','run-candidate-r2/result.json']
if '--final' in sys.argv:
 names+=['evidence/'+n for n in ['result.json','next-boundary-public.txt','boot-boundary-lines.txt','observer-boundary-lines.txt','runtime-resume-result.json','base-unchanged-receipt.json']]
 names+=['run-runtime/'+n for n in ['status.json','command.json','explicit-fatal-guard.json','framework-boundary-stop.json']]
script='from pathlib import Path\nimport json\nR=Path("/srv/android/asus-vendor-bpf-load-compat-20261107")\nnames='+repr(names)+'\nprint(json.dumps({n:(R/n).read_text() for n in names if (R/n).exists()}))\n'
d=json.loads(run(script))
for n,t in d.items():
 p=L/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
print('public_files',len(d),'bytes',sum(len(t.encode()) for t in d.values()))
