from pathlib import Path
import os,json
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');R.mkdir(exist_ok=False)
for n in ['source','evidence','inputs','tmp','work','patches']: (R/n).mkdir()
os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
names=[p.name for p in Path('/srv/android').iterdir() if any(s in p.name.lower() for s in ['graphics','linker','surface','firstboot','runtime','native-cache'])]
print(json.dumps(names,indent=2));(R/'evidence/discovery.json').write_text(json.dumps(names,indent=2))
