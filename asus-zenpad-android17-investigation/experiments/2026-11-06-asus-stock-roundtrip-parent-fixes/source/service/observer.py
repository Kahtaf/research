"""Same-run read-only USB observer. Transport loss never dispatches entry or writes."""
from __future__ import annotations
import copy,math,re,threading,time
from pathlib import Path
import fixed as F

class Unavailable(Exception):pass
class IdentityError(F.Refused):pass
UUID=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

def inventory(text):
 rows=[]
 for line in text.splitlines():
  if not line or line=='List of devices attached':continue
  words=line.split();F.require(len(words)>=2 and not words[0].startswith('*'),'Malformed ADB inventory')
  row={'serial':words[0],'state':words[1]}
  for word in words[2:]:
   F.require(':' in word,'Malformed inventory field');k,v=word.split(':',1)
   F.require(k not in row and v,'Duplicate/empty inventory field');row[k]=v
  rows.append(row)
 return rows

def usb_row(rows,pin=None):
 candidates=[r for r in rows if r['serial'] in (F.SERIAL,F.DIAG_SERIAL) or (pin and r.get('usb')==pin['usb'])]
 if not candidates:return None
 if len(candidates)!=1:raise IdentityError('Ambiguous stock/diagnostic USB devices')
 r=candidates[0]
 if pin and r.get('usb')!=pin['usb']:raise IdentityError('Physical USB topology missing or changed')
 if r['state'] in ('offline','unauthorized'):
  return None
 F.require(r.get('usb') and re.fullmatch(r'[0-9]+',r.get('transport_id','')),'USB topology/transport ID required')
 expected=F.STOCK_ROW if r['serial']==F.SERIAL else F.DIAG_ROW
 if any(r.get(k)!=v for k,v in expected.items()):raise IdentityError('USB identity/state mismatch')
 return r

def stock_ready(s):
 for k,v in F.STOCK_PROPS.items():
  if k=='sys.boot_completed':continue
  if s.get(k)!=v:raise IdentityError('Stock property mismatch: '+k)
 for k,v in {'enforce':'Enforcing','uid':'2000','context':'u:r:shell:s0','kernel':F.KERNEL_BANNER}.items():
  if s.get(k)!=v:raise IdentityError('Stock health mismatch: '+k)
 if not UUID.fullmatch(s.get('boot_id','')):raise IdentityError('Invalid stock boot ID')
 return s.get('sys.boot_completed')=='1' and s.get('flash_recovery')=='stopped'

def make_pin(io,run_id,process_nonce,clock=time.monotonic):
 F.valid_run(run_id)
 row=usb_row(io.inventory())
 F.require(row is not None and row['serial']==F.SERIAL,'Fresh normal stock USB enumeration required')
 s=io.stock_snapshot(row)
 F.require(stock_ready(s),'Stock Android not boot-complete / autorepair still active')
 F.require(usb_row(io.inventory())==row,'USB enumeration changed during pin capture')
 return dict(schema_version=2,run_id=run_id,process_nonce=process_nonce,created_monotonic=clock(),
  stock_boot_id=s['boot_id'],usb=row['usb'],initial_transport_id=row['transport_id'],stock_row=row,
  stock_snapshot=s,candidate_full_sha256=F.FULL_SHA,kernel_sha256=F.KERNEL_SHA)

def validate_pin(pin,run_id,process_nonce,now):
 F.require(set(pin)=={'schema_version','run_id','process_nonce','created_monotonic','stock_boot_id','usb',
  'initial_transport_id','stock_row','stock_snapshot','candidate_full_sha256','kernel_sha256'},'Unexpected pin schema')
 F.require(type(pin['schema_version']) is int and pin['schema_version']==2,'Wrong pin version')
 F.require(pin['run_id']==run_id and pin['process_nonce']==process_nonce,'Pin belongs to a different run/process')
 age=now-pin['created_monotonic']
 F.require(type(pin['created_monotonic']) in (int,float) and math.isfinite(age) and 0<=age<=30,'Stale/future pin')
 F.require(pin['candidate_full_sha256']==F.FULL_SHA and pin['kernel_sha256']==F.KERNEL_SHA,'Pin image/kernel mismatch')
 F.require(stock_ready(pin['stock_snapshot']) and pin['stock_snapshot']['boot_id']==pin['stock_boot_id'],'Pin health mismatch')
 row=usb_row([pin['stock_row']]);F.require(row['serial']==F.SERIAL and row['usb']==pin['usb'] and row['transport_id']==pin['initial_transport_id'],'Pin enumeration mismatch')


def report(data,rc):
 result={'classification':'invalid','errors':[],'exit_status':rc,'sha256':F.sha(data),'bytes':len(data)}
 def err(message):result['errors'].append(message)
 if len(data)>256*1024:err('oversized_report');return result
 try:text=data.decode('utf-8')
 except UnicodeDecodeError:err('non_utf8');return result
 # ADB may translate LF to CRLF; no other text normalization is accepted.
 text=text.replace('\r\n','\n');lines=text.splitlines()
 endpoint='REPORT_ENDPOINT uid=2000 context=u:r:shell:s0'
 if not lines or lines[0]!=endpoint or lines.count(endpoint)!=1:err('endpoint_identity')
 if lines.count(F.MARKER)!=1:err('marker_missing_or_duplicate')
 if lines.count('[ /tmp/diagnostic.txt ]')!=1:err('report_file_boundary')
 ends=[i for i,x in enumerate(lines) if x=='END_DIAGNOSTIC']
 if not ends:
  err('missing_END');result['classification']='partial' if lines and lines[0]==endpoint else 'invalid';return result
 if len(ends)!=1 or any(x for x in lines[ends[0]+1:]):err('END_not_unique_final')
 if rc!=0:err('command_failed')
 # The terminator is protocol framing, never the last section's content.
 text='\n'.join(lines[:ends[0]])+'\n'
 matches=list(re.finditer(r'^\[ ([^\n]+) \]\n',text,re.M));sections={}
 for i,m in enumerate(matches):
  key=m.group(1)
  if key in sections:err('duplicate_section:'+key)
  sections[key]=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip('\n')
 def value(path):
  if path not in sections:err('missing_section:'+path);return ''
  return sections[path].strip()
 if value('/proc/version')!=F.KERNEL_BANNER:err('stock_kernel_banner_mismatch')
 tokens=value('/proc/cmdline').split()
 serial=[x for x in tokens if x.startswith('androidboot.serialno=')]
 if serial!=['androidboot.serialno='+F.SERIAL]:err('cmdline_serial_not_exact_unique')
 if any(x in ('enforcing=0','selinux=0','androidboot.selinux=permissive') for x in tokens):err('permissive_cmdline')
 if value('/sys/fs/selinux/enforce')!='1':err('not_enforcing')
 context=value('/proc/self/attr/current')
 if context not in ('u:r:recovery:s0','u:r:recovery:s0\x00'):err('collector_domain')
 uptime=value('/proc/uptime').split()
 try:
  nums=[float(x) for x in uptime]
  if len(nums)!=2 or not all(math.isfinite(x) and x>=0 for x in nums) or nums[0]>150:err('uptime_invalid_or_stale')
 except ValueError:err('uptime_invalid')
 mounts=value('/proc/mounts')
 if not mounts:err('missing_mounts')
 for line in mounts.splitlines():
  parts=line.split()
  if len(parts)!=6:err('malformed_mounts');continue
  if parts[0].startswith('/dev/block/') or parts[1] in ('/data','/system','/cache','/persist','/metadata'):err('persistent_mount')
 if not result['errors']:
  result.update(classification='diagnostic_pass',kernel_banner_verified=True,enforcing_verified=True,
                endpoint_uid_domain_verified=True,cmdline_serial_verified=True,complete=True)
 return result

class Observer:
 """One readiness handshake and one bounded observation; no imported saved pins."""
 def __init__(self,io,pin,run_id,nonce,directory,clock=time.monotonic):
  self.io=io;self.pin=copy.deepcopy(pin);self.run_id=run_id;self.nonce=nonce;self.directory=directory;self.clock=clock
  validate_pin(pin,run_id,nonce,clock());directory.mkdir(mode=0o700,exist_ok=False)
  self.ready=threading.Event();self.armed=threading.Event();self.cancelled=threading.Event();self.lock=threading.RLock()
  self.entry_at=None;self.end=None;self.thread=None
  self.state=dict(schema_version=2,run_id=run_id,ready=False,entry_armed=False,diagnostic_seen=False,
   report_classification='not_observed',diagnostic_pass=False,stock_returned=False,stock_return=None,
   disconnect_observed=False,restore_verified=False,pin=pin,events=[],error=None)
  self.save()
 def save(self):F.durable(self.directory/'state.json',self.state)
 def event(self,kind,**kw):
  with self.lock:self.state['events'].append(dict(monotonic=self.clock(),kind=kind,**kw));self.save()
 def start(self):
  self.thread=threading.Thread(target=self.run,name='stock-read-only-usb-observer',daemon=True);self.thread.start()
  if not self.ready.wait(20):self.cancelled.set();raise F.Unknown('Observer did not become ready before entry')
  F.require(self.state['ready'] and not self.state['error'],'Observer readiness failed: '+str(self.state['error']))
 def arm(self):
  validate_pin(self.pin,self.run_id,self.nonce,self.clock())
  F.require(self.state['ready'] and self.entry_at is None and not self.state['error'],'Observer cannot arm entry')
  self.entry_at=self.clock();self.end=self.entry_at+420
  with self.lock:self.state['entry_armed']=True;self.state['entry_monotonic']=self.entry_at;self.save()
  self.armed.set()
 def stop(self):
  self.cancelled.set()
  if self.thread:self.thread.join(15)
  if self.thread and self.thread.is_alive():raise F.Unknown('Observer thread did not stop; no device mutation')
 def wait(self):
  F.require(self.entry_at is not None,'Observer never armed')
  self.thread.join(max(0,self.end-self.clock())+15)
  if self.thread.is_alive():self.cancelled.set();raise F.Unknown('Observer exceeded bounded observation')
  return copy.deepcopy(self.state)
 def run(self):
  try:
   row=usb_row(self.io.inventory(),self.pin)
   F.require(row==self.pin['stock_row'],'Observer initial enumeration differs from fresh pin')
   s=self.io.stock_snapshot(row)
   F.require(stock_ready(s) and s['boot_id']==self.pin['stock_boot_id'],'Observer initial stock health changed')
   with self.lock:self.state['ready']=True;self.save()
   self.ready.set()
   while not self.armed.wait(.1):
    if self.cancelled.is_set():return
    validate_pin(self.pin,self.run_id,self.nonce,self.clock())
   attempts={};last_report={}
   while self.clock()<self.end and not self.cancelled.is_set():
    remaining=self.end-self.clock()
    rows=self.io.inventory(timeout=min(8,remaining));row=usb_row(rows,self.pin)
    if row is None:
     if not self.state['disconnect_observed']:
      with self.lock:self.state['disconnect_observed']=True
      self.event('expected_disconnect_observed')
    elif row['serial']==F.DIAG_SERIAL:
     F.require(row['transport_id']!=self.pin['initial_transport_id'],'Diagnostic reused pre-entry transport ID')
     with self.lock:self.state['diagnostic_seen']=True
     tid=row['transport_id'];n=attempts.get(tid,0)
     if not self.state['diagnostic_pass'] and n<4 and self.clock()-last_report.get(tid,-1e9)>=5:
      attempts[tid]=n+1;last_report[tid]=self.clock()
      try:p=self.io.report(row,timeout=min(12,max(.1,self.end-self.clock())))
      except Unavailable as exc:
       self.event('report_transport_unavailable',transport_id=tid,error=str(exc))
      else:
       assessment=report(p.stdout,p.returncode)
       file=self.directory/f'report-{tid}-{n+1}.txt'
       with file.open('xb') as f:f.write(p.stdout)
       with self.lock:
        self.state['report_classification']=assessment['classification']
        self.state['diagnostic_pass']=assessment['classification']=='diagnostic_pass'
       self.event('report_attempt',transport_id=tid,file=file.name,assessment=assessment)
    else:
     try:s=self.io.stock_snapshot(row,timeout=min(8,max(.1,self.end-self.clock())))
     except Unavailable as exc:
      self.event('stock_snapshot_unavailable',transport_id=row['transport_id'],error=str(exc));s=None
     if s is not None and stock_ready(s) and s['boot_id']!=self.pin['stock_boot_id']:
      F.require(row['transport_id']!=self.pin['initial_transport_id'],'Stock new boot reused pre-entry transport ID')
      elapsed=self.clock()-self.entry_at
      with self.lock:
       self.state.update(stock_returned=True,stock_return=dict(row=row,snapshot=s,elapsed_seconds=elapsed),
         return_timing_consistent_with_120s_deadline=120<=elapsed<=420)
      self.event('actual_new_stock_boot_verified',report_classification=self.state['report_classification'])
      return
    self.cancelled.wait(min(2,max(0,self.end-self.clock())))
   self.event('observation_cancelled' if self.cancelled.is_set() else 'observation_deadline_no_reset_inferred')
  except BaseException as exc:
   with self.lock:self.state['error']=f'{type(exc).__name__}: {exc}';self.save()
  finally:self.ready.set()
