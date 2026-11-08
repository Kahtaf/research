#!/usr/bin/env python3
import sys,subprocess,pathlib,json,datetime
from remote import SSH
R=pathlib.Path(__file__).resolve().parents[1]
script=r'''
import os,pathlib,datetime,json
now=datetime.datetime.now(datetime.timezone.utc).isoformat(); root=pathlib.Path('/srv/android')
jobs={}
for name,folder,prefix in [('full-r5','asus-device-product','full-build-r5'),('combined-r1','asus-build-continuation','kernel-r1')]:
 base=root/folder/'logs'; p=base/(prefix+'.pid');pid=int(p.read_text()) if p.exists() else None
 record={'pid':pid,'markers':{s:(base/(prefix+'.'+s)).read_text() for s in ['started','exit-code','finished','complete'] if (base/(prefix+'.'+s)).exists()}}
 if pid and pathlib.Path('/proc',str(pid)).exists():
  record['proc_stat']=pathlib.Path('/proc',str(pid),'stat').read_text();record['cmdline']=pathlib.Path('/proc',str(pid),'cmdline').read_bytes().replace(b'\0',b' ').decode();record['alive']=True
 else:record['alive']=False
 log=base/(prefix+'.log')
 if log.exists():
  record['log_bytes']=log.stat().st_size
  with log.open('rb') as f:f.seek(max(0,log.stat().st_size-2500));record['log_tail']=f.read().decode(errors='replace')
 jobs[name]=record
print(json.dumps({'utc':now,'vm_boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'jobs':jobs},indent=2))
'''
p=subprocess.run(SSH+['python3 -'],input=script.encode(),capture_output=True,check=True);obj=json.loads(p.stdout)
name=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
(R/'evidence'/('process-'+name+'.json')).write_bytes(p.stdout)
(R/'evidence/current-processes.json').write_bytes(p.stdout)
for n,v in obj['jobs'].items():print(n,'alive=',v['alive'],'markers=',v['markers'],'log_bytes=',v.get('log_bytes'),v.get('log_tail','')[-600:])
