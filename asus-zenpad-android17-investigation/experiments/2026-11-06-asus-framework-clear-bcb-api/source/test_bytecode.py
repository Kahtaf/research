"""Interpret selected ORIGINAL OEM DEX instruction streams with explicit stubs.
This is a narrow Dalvik subset interpreter, not ART or Binder/kernel execution.
No device, network, socket, property service, UID/context change, or block I/O.
"""
from pathlib import Path
import json,hashlib,resource
from dex import Dex
from disasm_dex import decode
S=Path(__file__).resolve().parents[1]
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
F='Landroid/os/IRecoverySystem$Stub;';B='Lcom/android/server/RecoverySystemService$BinderService;';P='Landroid/os/IRecoverySystem$Stub$Proxy;'
INDEX=json.loads((S/'evidence/decoded-methods.json').read_text());DEX={name:Dex(S/name) for name in {m['file'] for m in INDEX}}
METHODS={}
for item in INDEX:
 d=DEX[item['file']];code=d.code(item['code']['code_offset']);rows=decode(d,code)
 assert rows==item['instructions'];METHODS[item['method']]=(code,{r['pc']:r for r in rows})
for r in json.loads((S/'evidence/dex-extraction.json').read_text()):assert hashlib.sha256((S/r['file']).read_bytes()).hexdigest()==r['sha256']
class Fault(Exception):
 def __init__(self,kind,message=''):self.kind=kind;self.message=message
class VM:
 def __init__(self,uid=0,status=100,**options):
  self.uid=uid;self.status=status;self.options=options;self.events=[];self.stubs=set();self.trace=[];self.steps=0;self.connects=0
  self.context={'class':'Landroid/app/ContextImpl;'};self.ams={'class':'Lcom/android/server/am/ActivityManagerService;'}
  self.owner={'class':'Lcom/android/server/RecoverySystemService;','mContext':self.context}
  self.binder={'class':B,'this$0':self.owner};self.proxy={'class':P,'mRemote':self.binder}
 def method(self,cl,name):return next(k for k in METHODS if k.startswith(cl+'->'+name+'('))
 def call(self,ref,args,style):
  key=ref
  if style.startswith('invoke-virtual') or style.startswith('invoke-interface'):
   if args and isinstance(args[0],dict) and 'class' in args[0]:
    dynamic=args[0]['class']+'->'+ref.split('->')[1]
    if dynamic in METHODS:key=dynamic
  if key in METHODS:return self.run(key,args)
  self.stubs.add(ref)
  cl,name=ref.split('->');method=name.split('(')[0]
  if ref=='Landroid/os/Binder;->getCallingUid()I':return self.uid
  if ref=='Landroid/os/Binder;->getCallingPid()I':return 1234
  if ref=='Landroid/app/ActivityManagerNative;->getDefault()Landroid/app/IActivityManager;':return self.ams
  if ref=='Landroid/os/UserHandle;->isIsolated(I)Z':return 0
  if ref=='Landroid/app/AppGlobals;->getPackageManager()Landroid/content/pm/IPackageManager;':return {'class':'fixture-package-manager'}
  if cl=='Landroid/content/pm/IPackageManager;' and method=='checkUidPermission':
   assert args[1]=='android.permission.RECOVERY';self.events.append({'package_permission_stub_uid':args[2]});return self.options.get('package_grant',-1)
  if cl=='Landroid/os/SystemProperties;' and method=='set':
   assert args==['ctl.start','clear-bcb'];self.events.append({'property_set_stub':args})
   if self.options.get('property_denied'):raise Fault('Ljava/lang/RuntimeException;','fixture property denial')
   return None
  if cl=='Landroid/net/LocalSocket;' and method=='connect':
   assert args[1]['address']=='uncrypt' and args[1]['namespace']=='RESERVED';self.connects+=1;self.events.append({'connect_stub':self.connects,'address':'RESERVED:uncrypt'})
   if self.connects<=self.options.get('connect_failures',0):raise Fault('Ljava/io/IOException;','fixture connect failure')
   return None
  if cl=='Landroid/net/LocalSocket;' and method in ('getInputStream','getOutputStream'):return {'class':'fixture-stream','direction':method}
  if cl=='Ljava/lang/Thread;' and method=='sleep':assert args==[1000,0];self.events.append({'sleep_stub_ms':1000});return None
  if cl=='Ljava/io/DataInputStream;' and method=='readInt':
   if self.options.get('read_error'):raise Fault('Ljava/io/IOException;','fixture read failure')
   data=self.status.to_bytes(4,'big',signed=True);self.events.append({'status_bytes_stub':data.hex()});return int.from_bytes(data,'big',signed=True)
  if cl=='Ljava/io/DataOutputStream;' and method=='writeInt':
   assert args[1]==0;self.events.append({'ack_bytes_stub':bytes(4).hex()})
   if self.options.get('ack_error'):raise Fault('Ljava/io/IOException;','fixture ack failure')
   return None
  if cl=='Llibcore/io/IoUtils;' and method=='closeQuietly':self.events.append({'close_stub':args[0].get('class') if isinstance(args[0],dict) else None});return None
  if cl=='Landroid/util/Slog;':return 0
  if cl=='Ljava/lang/StringBuilder;':
   if method=='<init>':args[0]['text']='';return None
   if method=='append':args[0]['text']+=str(args[1]);return args[0]
   if method=='toString':return args[0]['text']
  if method=='<init>' and cl in ('Landroid/net/LocalSocket;','Ljava/io/DataInputStream;','Ljava/io/DataOutputStream;','Ljava/lang/IllegalArgumentException;','Ljava/lang/SecurityException;'):return None
  if cl=='Landroid/net/LocalSocketAddress;' and method=='<init>':args[0].update(address=args[1],namespace=args[2]);return None
  if cl=='Landroid/os/Parcel;':
   if method=='obtain':return {'class':cl,'ints':[],'token':None,'strings':[]}
   if method=='writeInterfaceToken':args[0]['token']=args[1];return None
   if method=='enforceInterface':
    self.events.append({'enforce_interface':args[1]})
    if args[0]['token']!=args[1]:raise Fault('Ljava/lang/SecurityException;','bad descriptor')
    return None
   if method=='writeNoException':args[0]['ints'].append(0);return None
   if method=='writeInt':args[0]['ints'].append(args[1]);return None
   if method=='writeString':args[0]['strings'].append(args[1]);return None
   if method=='readInt':return args[0]['ints'].pop(0)
   if method=='readException':assert args[0]['ints'].pop(0)==0;return None
   if method=='recycle':return None
  if cl=='Landroid/os/IBinder;' and method=='transact':
   remote,code,data,reply,flags=args;assert code==3 and flags==0 and data['token']=='android.os.IRecoverySystem' and data['ints']==[] and data['strings']==[]
   self.events.append({'binder_transact_stub':code,'flags':flags,'no_method_arguments':True});return self.run(self.method(F,'onTransact'),[remote,code,data,reply,flags])
  if cl=='Landroid/os/Binder;' and method=='onTransact':return 0
  raise AssertionError(('unapproved external call',ref,args))
 def run(self,key,args):
  code,rows=METHODS[key];assert len(args)==code['ins'],(key,args,code['ins']);r=[0]*code['registers'];r[-len(args):]=args;pc=0;last=None;exception=None
  while True:
   self.steps+=1;assert self.steps<30000,'instruction budget';x=rows[pc];self.trace.append([key,pc]);n=x['name'];v=x['registers'];nxt=pc+x['width']
   try:
    if n.startswith('const-string'):r[v[0]]=x['ref']
    elif n.startswith('const-wide'):r[v[0]]=x['literal']&0xffffffff;r[v[0]+1]=(x['literal']>>32)&0xffffffff
    elif n.startswith('const'):r[v[0]]=x['literal']
    elif n.startswith('move-result'):r[v[0]]=last
    elif n=='move-exception':r[v[0]]=exception
    elif n.startswith('move'):r[v[0]]=r[v[1]]
    elif n=='new-instance':r[v[0]]={'class':x['ref']}
    elif n=='iget-object':r[v[0]]=r[v[1]][x['ref'].split('->')[1].split(':')[0]]
    elif n.startswith('sget'):
     ref=x['ref']
     if '->MY_PID:' in ref:r[v[0]]=999
     elif '->DEBUG_PERMISSION:' in ref:r[v[0]]=0
     elif '->RESERVED:' in ref:r[v[0]]='RESERVED'
     else:raise AssertionError(('unexpected static',ref))
    elif n.startswith('invoke-'):last=self.call(x['ref'],[r[i] for i in v],n)
    elif n.startswith('if-'):
     a=r[v[0]];b=r[v[1]] if len(v)==2 else 0
     op=n[3:];op=op[:-1] if op.endswith('z') else op
     ok={'eq':lambda:a==b,'ne':lambda:a!=b,'lt':lambda:a<b,'ge':lambda:a>=b,'gt':lambda:a>b,'le':lambda:a<=b}[op]()
     if ok:nxt=x['target']
    elif n.startswith('goto'):nxt=x['target']
    elif n in ('sparse-switch','packed-switch'):nxt=x['switch'].get(str(r[v[0]]),nxt)
    elif n=='rem-int':r[v[0]]=r[v[1]]%r[v[2]]
    elif n=='add-int/lit8':r[v[0]]=r[v[1]]+x['literal']
    elif n=='return-void':return None
    elif n.startswith('return'):return r[v[0]]
    elif n=='throw':
     value=r[v[0]]
     if isinstance(value,Fault):raise value
     raise Fault(value['class'])
    elif n=='nop':pass
    else:raise AssertionError(('unimplemented actual opcode',n))
   except Fault as fault:
    handler=None
    for item in code['try_items']:
     if item['start']<=pc<item['end']:
      for ty,target in item['handlers']:
       if ty in (fault.kind,'any'):handler=target;break
      break
    if handler is None:raise
    exception=fault;nxt=handler
   pc=nxt

def scenario(name,uid=0,status=100,expected=1,**options):
 vm=VM(uid,status,**options);exception=None;reply={'class':'Landroid/os/Parcel;','ints':[],'strings':[]};token=options.get('token','android.os.IRecoverySystem')
 try:
  if options.get('proxy'):result=vm.run(vm.method(P,'clearBcb'),[vm.proxy]);returned=result
  else:
   code=options.get('transaction',3);result=vm.run(vm.method(F,'onTransact'),[vm.binder,code,{'class':'Landroid/os/Parcel;','token':token},reply,0]);returned=reply['ints'][1] if len(reply['ints'])==2 else result
 except Fault as f:exception=f.kind;returned='exception'
 assert returned==expected,(name,returned,reply,vm.events)
 props=[e for e in vm.events if 'property_set_stub'in e];acks=[e for e in vm.events if 'ack_bytes_stub'in e]
 if options.get('transaction')==1598968902:assert reply['strings']==['android.os.IRecoverySystem'] and not props
 elif expected=='exception':
  if options.get('property_denied'):assert len(props)==1 and vm.connects==0
  else:assert not props and vm.connects==0
 else:
  assert len(props)==1 and all(e['property_set_stub']==['ctl.start','clear-bcb'] for e in props)
  assert vm.connects==min(options.get('connect_failures',0)+1,30)
  if vm.connects==30 and options.get('connect_failures',0)>=30:assert not acks
  elif not options.get('read_error'):assert acks==[{'ack_bytes_stub':'00000000'}]
 return dict(name=name,uid=uid,status=status,returned=returned,exception=exception,steps=vm.steps,connect_attempts=vm.connects,events=vm.events,stubs=sorted(vm.stubs),executed_pcs=sorted({(k,p) for k,p in vm.trace}))

if __name__=='__main__':
 results=[scenario('root_success'),scenario('root_oem_failure',status=-1,expected=0),scenario('root_unexpected_status',status=7,expected=0),scenario('root_read_failure',expected=0,read_error=True),scenario('root_ack_failure',expected=0,ack_error=True),scenario('root_connect_then_success',connect_failures=2),scenario('root_connect_exhausted',expected=0,connect_failures=30),scenario('property_failure',expected='exception',property_denied=True),scenario('wrong_descriptor',expected='exception',token='not.the.interface'),scenario('unprivileged_denied',uid=2000,expected='exception'),scenario('system_uid_permission_path',uid=1000),scenario('proxy_oem_failure',proxy=True,status=-1,expected=0),scenario('proxy_wire_shape',proxy=True),scenario('descriptor_only',transaction=1598968902)]
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;assert peak<1024**3
 (S/'evidence/bytecode-tests.json').write_text(json.dumps(dict(passed=len(results),peak_rss_bytes=peak,boundary='Narrow interpreter executes original decoded instructions; explicit external Java/Parcel/socket/property fixtures. No ART/JNI/kernel/Binder/device execution.',cases=results),indent=2)+'\n')
 print(json.dumps({'passed':len(results),'peak_rss_bytes':peak}))
