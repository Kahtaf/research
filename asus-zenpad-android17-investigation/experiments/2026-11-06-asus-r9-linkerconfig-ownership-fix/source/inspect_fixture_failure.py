from pathlib import Path
import os,subprocess as s,json,re
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');fc=(R/'inputs/root-enabled-plat_file_contexts').read_text();d={'context_matches':{},'data_metadata':{}}
for path in ['/data','/data/local','/data/local/tmp','/data/local/tmp/actual-runtime-report.txt','/apex/com.android.runtime/bin','/system/etc/runtime-bin/linker','/system/etc/runtime-bin/linker64','/system/etc/runtime-bin/linkerconfig','/system/bin/linker','/system/bin/linker64']:
 rows=[]
 for line in fc.splitlines():
  a=line.split()
  if not a or line.startswith('#'):continue
  try:
   if re.fullmatch(a[0],path):rows.append(line)
  except re.error:pass
 d['context_matches'][path]=rows
D=Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');env=os.environ.copy();env['LD_LIBRARY_PATH']=str(D.parents[1]/'lib64')
for path in ['/','/local','/local/tmp','/local/tmp/actual-runtime-report.txt']:
 p=s.run([str(D),'-R','stat '+path,str(R/'inputs/runtime-r1/data.ext4')],env=env,capture_output=True,text=True,timeout=15);d['data_metadata'][path]=p.stdout+p.stderr
log=(R/'run-runtime-r1/serial.log').read_text();d['observer_lines']=[x for x in log.splitlines() if 'actual-runtime-observer' in x or ('222:' in x and 'binder' in x)];(R/'evidence/fixture-r1-failure-inspection.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
