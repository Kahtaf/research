from pathlib import Path
import subprocess,json,datetime,os
R=Path('/srv/android/asus-firstboot-parity-continuation')
O=R/'evidence/parity-run.json'; assert not O.exists()
rows=[]
for script,args in [('run_cpuset_probe.py',['r3','r7']),('run_locks_probe.py',['r1','r7']),('run_policy.py',[]),('run_boot_r11.py',['r11'])]:
 cmd=['python3',str(R/'source'/script),*args]; row={'command':cmd,'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}; rows.append(row)
 with (R/'evidence'/(script+'.log')).open('w') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);row['pid']=p.pid;O.write_text(json.dumps(rows,indent=2));row['returncode']=p.wait()
 row['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();O.write_text(json.dumps(rows,indent=2))
 print(script,row['returncode'],flush=True)
 if row['returncode']: break
