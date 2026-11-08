"""Read complete retained console and saved fiq once, bound to the returned stock boot."""
from pathlib import Path
import datetime,fcntl,hashlib,importlib.util,json,os,re,secrets,subprocess
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
spec=importlib.util.spec_from_file_location('collector',WORK/'2026-11-07-asus-usb-retained-log-collector/scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def main():
 os.umask(0o077)
 trial=json.loads((ROOT/'evidence/recovery-entry.json').read_text())
 assert trial['normal_android_return_proven'] and trial['new_stock_boot_id']!=trial['previous_boot_id']
 boot=trial['new_stock_boot_id'];out=ROOT/'evidence/RESULT.json';assert not out.exists()
 assert hashlib.sha256(c.HELPER.read_bytes()).hexdigest()==c.HELPER_SHA
 for name,h in c.SHIM_PINS.items():assert hashlib.sha256((c.SHIM/name).read_bytes()).hexdigest()==h
 token=secrets.token_hex(16);marks=['ASUS_READ_'+token+'_'+x for x in ('LOG_BEGIN','LOG_END','FIQ_BEGIN','FIQ_END')]
 script='[ "$(cat /proc/sys/kernel/random/boot_id)" = '+boot+' ]\n[ -f /proc/last_kmsg ]\n[ ! -L /proc/last_kmsg ]\n'
 script+='printf "\\n'+marks[0]+'\\n"\ndd if=/proc/last_kmsg bs=4096 count=513 2>/dev/null\nprintf "\\n'+marks[1]+'\\n"\n'
 script+='printf "\\n'+marks[2]+'\\n"\ndd if=/proc/aed/reboot-reason bs=4096 count=8 2>/dev/null\nprintf "\\n'+marks[3]+'\\n"\n'
 script+='[ "$(cat /proc/sys/kernel/random/boot_id)" = '+boot+' ]\n'
 env={k:v for k,v in os.environ.items() if not k.startswith(('ADB_','ANDROID_ADB_')) and k!='ANDROID_SERIAL'}
 env['PATH']=str(c.SHIM)+os.pathsep+'/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools'+os.pathsep+env.get('PATH','/usr/bin:/bin')
 state={'outcome':'UNKNOWN','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boot_id':boot,'candidate_p10_sha256':trial['candidate_p10_sha256'],'image_writes':False,'root_command_reads_only':True,'preserved_helper_staging':True,'no_reboot_retry':True}
 with (WORK/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  (ROOT/'private/read-intent.json').write_text(json.dumps(state,indent=2)+'\n')
  try:
   q=subprocess.run(['python3','-B',str(c.HELPER)],input=script.encode(),env=env,capture_output=True,timeout=90)
   (ROOT/'private/read.stdout').write_bytes(q.stdout);(ROOT/'private/read.stderr').write_bytes(q.stderr)
   state['helper_exit']=q.returncode
   data=q.stdout.replace(b'\r\n',b'\n');assert q.returncode==0,'Root read or Enforcing restoration failed'
   blocks=[]
   for start,end,limit in [(marks[0],marks[1],2097152),(marks[2],marks[3],32768)]:
    first=('\n'+start+'\n').encode();last=('\n'+end+'\n').encode()
    assert data.count(first)==1 and data.count(last)==1,'Fresh read delimiters absent/ambiguous'
    block=data.split(first,1)[1].split(last,1)[0];assert len(block)<=limit
    blocks.append(block)
   log,fiq=blocks
   (ROOT/'private/last_kmsg.txt').write_bytes(log);(ROOT/'private/reboot-reason.txt').write_bytes(fiq)
   before=re.findall(rb'A7_READ=(\d+) ',log);after=re.findall(rb'fiq step:\s*(\d+)',fiq)
   assert len(after)==1,'Saved fiq absent/ambiguous'
   state.update(complete_console_read=True,console_bytes=len(log),console_sha256=hashlib.sha256(log).hexdigest(),saved_fiq=int(after[0]),before_reset_values=[int(x) for x in before],enforcing_restored=True)
   if len(before)!=1:state['outcome']='UNKNOWN_BEFORE_RESET_READBACK'
   elif int(before[0])==167 and int(after[0])==167:state['outcome']='CALIBRATED_THIS_SEQUENCE'
   elif int(before[0])==167:state['outcome']='CURRENT_WRITTEN_SAVED_NONMATCH'
   else:state['outcome']='CURRENT_READBACK_NONMATCH'
   state['diagnostic_lines']=[x.decode('utf-8','replace') for x in log.splitlines() if b'A7_READ=' in x]+[x.decode('utf-8','replace') for x in fiq.splitlines() if b'fiq step:' in x]
  except BaseException as e:state['error']=type(e).__name__+': '+str(e)
  state['missing_marker_does_not_prove_linux49_nonexecution']=True
  with out.open('x') as f:
   json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(state),flush=True)
 return 2 if state['outcome'].startswith('UNKNOWN') else 0
if __name__=='__main__':raise SystemExit(main())
