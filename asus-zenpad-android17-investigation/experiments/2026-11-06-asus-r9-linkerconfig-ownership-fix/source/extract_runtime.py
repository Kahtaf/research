from pathlib import Path
import os,json,subprocess as s,hashlib,re,base64
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');I=R/'inputs/runtime-r1';E=R/'evidence';os.environ['TMPDIR']=str(R/'tmp');assert (R/'run-runtime-r1/status.json').is_file();debug=Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');env=os.environ.copy();env['LD_LIBRARY_PATH']=str(debug.parents[1]/'lib64');cmds=[]
for cmd in ['stat /local/tmp/actual-runtime-report.txt','ea_list /local/tmp/actual-runtime-report.txt','dump /local/tmp/actual-runtime-report.txt '+str(E/'actual-runtime-report.txt')]:
 p=s.run([str(debug),'-R',cmd,str(I/'data.ext4')],env=env,capture_output=True,text=True,timeout=15);cmds.append(dict(command=cmd,rc=p.returncode,stdout=p.stdout,stderr=p.stderr))
(E/'data-report-extraction.json').write_text(json.dumps(cmds,indent=2));serial=(R/'run-runtime-r1/serial.log').read_text();report=(E/'actual-runtime-report.txt').read_text() if (E/'actual-runtime-report.txt').is_file() else '';lines=[]
for name,text in [('serial',serial),('scratch',report)]:
 for i,line in enumerate(text.splitlines(),1):
  if any(x in line for x in ['linkerconfig','enforce','IPC_FUNCTIONAL','IPC_REPLY','ro.debuggable','ro.secure','ro.adb.secure','keymaster@4.0','keymaster-4-0','keystore2','keystore.module','PUBLIC_','IKeymaster']):lines.append({'source':name,'line':i,'text':line})
(E/'runtime-highlights.json').write_text(json.dumps(lines,indent=2));print(json.dumps({'scratch_bytes':len(report),'highlights':lines[:120]},indent=2));os.chmod(I/'data.ext4',0o444)
