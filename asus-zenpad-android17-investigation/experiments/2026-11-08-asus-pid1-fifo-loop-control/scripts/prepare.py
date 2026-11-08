from pathlib import Path
import ast,difflib,hashlib,json,re,shutil,sys,uuid
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-08-asus-sparse-watchdog-observation';H=W/'2026-11-07-asus-linux49-direct-clock-syscall-control'
sha=lambda d:hashlib.sha256(d).hexdigest()
assert sha((W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py').read_bytes())=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:shutil.copy2(B/'source'/n,R/'source'/n)
sys.path.insert(0,str(R/'source'));import bootformat as b
old=(B/'artifacts/candidate.img').read_bytes();full=(B/'artifacts/candidate.p10.raw').read_bytes()
assert sha(full)=='86213b3aabb8a003ff19157ba5b1dbb29377e0cb14cd70f896fdeccbb944792b' and full==old+bytes(b.PARTITION_SIZE-len(old))
h,k,ram,tail=b.parse_image(old);assert not tail and sha(ram)=='df6406bd884126190ce05c26f097f9d84a36c64e332286fa5aee6225670857d3'
cp,extra=b.ungzip(ram[512:]);assert not extra
helper=b.parse_cpio(cp)['init'][3];receipt=json.loads((H/'evidence/compiler-receipt.json').read_text());src=(H/'source/init.c').read_text()
assert sha(helper)==receipt['binary_sha256']=='1c9b6f23ed080be753b27ea49158564010a60cf2747e5964f07a2705e3745d1b'
assert sha(src.encode())==receipt['source_sha256']=='550dc7514d5bf95ca49440ef3dcc110f1e4594e99e9414f28ed3e287207312c6'
i=dict(kernel_uuid=str(uuid.uuid4()),helper_uuid=str(uuid.uuid4()),base_local=B.name,base_remote='/srv/android/asus-sparse-watchdog-observation-20261108-e0b1a1ba')
i['remote_root']='/srv/android/asus-pid1-fifo-loop-control-20261108-'+i['kernel_uuid'][:8]
i['mode']='ASUS49-MODE run='+i['kernel_uuid']+' profile=sparse-fifo-v1 hot=disabled ordinary_printk=filtered delay=original-virtual'
i['helper_prefix']='ASUS49-SYSCLOCK run='+i['helper_uuid']
(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
(R/'evidence/base-binding.json').write_text(json.dumps(dict(full_p10=sha(full),ramdisk=sha(ram),extracted_helper=sha(helper),source=sha(src.encode()),binding='Existing compiler receipt binds exact source to extracted binary; not a fresh rebuild of baseline',compiler_receipt=receipt),indent=2)+'\n')
(R/'source/base').mkdir()
(R/'source/base/init.c').write_text(src)
s=src.replace('f0c3c82c-d639-4d8a-90f2-155fd4224ceb',i['helper_uuid']).replace('#include <signal.h>','#include <signal.h>\n#include <sched.h>')
s=s.replace('static void observe(void){','static int observe(void){')
a='''  final=initial;reason="iteration-cap";
  while(iterations<2000000){'''
z='''  struct sched_param original={.sched_priority=-1},fifo={.sched_priority=1},actual={.sched_priority=-1};
  int policy=(int)syscall(SYS_sched_getscheduler,0),pe=policy<0?errno:0;
  int pr=(int)syscall(SYS_sched_getparam,0,&original),pre=pr<0?errno:0;char sv[192];
  snprintf(sv,sizeof(sv),"getparam_rc=%d getparam_errno=%d priority=%d",pr,pre,original.sched_priority);
  event("actual","sched.original","pid0",policy,pe,sv);
  if(policy!=SCHED_OTHER||pr||original.sched_priority!=0){
   event("invalid","sched.control","pid0",-1,0,"baseline-refused;require-SCHED_OTHER-priority0;no-RT-exposure");return -1;
  }
  int boost=(int)syscall(SYS_sched_setscheduler,0,SCHED_FIFO,&fifo),be=boost<0?errno:0;
  event("actual","sched.boost","pid0",boost,be,"requested_policy=1 requested_priority=1");
  int observed=(int)syscall(SYS_sched_getscheduler,0),oe=observed<0?errno:0;
  pr=(int)syscall(SYS_sched_getparam,0,&actual);pre=pr<0?errno:0;
  snprintf(sv,sizeof(sv),"getparam_rc=%d getparam_errno=%d priority=%d",pr,pre,actual.sched_priority);
  event("actual","sched.boost.observed","pid0",observed,oe,sv);
  int exposed=!boost&&observed==SCHED_FIFO&&!pr&&actual.sched_priority==1;
  if(!exposed)event("invalid","sched.control","pid0",-1,0,"boost-noop-or-control-invalid;no-accepted-RT-exposure");
  final=initial;reason="iteration-cap";
  if(exposed)while(iterations<2000000){'''
assert s.count(a)==1;s=s.replace(a,z)
a='''   if(delta<0){reason="counter-regressed";break;}'''
z='''   if(iterations==500000||iterations==1000000||iterations==1500000){
    char progress[96];snprintf(progress,sizeof(progress),"iterations=%u delta_ns=%lld",iterations,delta);
    event("actual","runnable.progress","CLOCK_MONOTONIC",0,0,progress);
   }
   if(delta<0){reason="counter-regressed";break;}'''
assert s.count(a)==1;s=s.replace(a,z)
a='''  }
 }else error=errno;'''
z='''  }
  int restore=(int)syscall(SYS_sched_setscheduler,0,policy,&original),re=restore<0?errno:0;
  event("actual","sched.restore","pid0",restore,re,"requested_policy=0 requested_priority=0");
  actual.sched_priority=-1;
  observed=(int)syscall(SYS_sched_getscheduler,0);oe=observed<0?errno:0;
  pr=(int)syscall(SYS_sched_getparam,0,&actual);pre=pr<0?errno:0;
  snprintf(sv,sizeof(sv),"getparam_rc=%d getparam_errno=%d priority=%d",pr,pre,actual.sched_priority);
  event("actual","sched.restored","pid0",observed,oe,sv);
  if(restore||observed!=policy||pr||actual.sched_priority!=original.sched_priority){
   event("invalid","sched.control","pid0",-1,0,"restore-failed-or-unverified;finish-reboot-attempt;no-retry");return -1;
  }
  if(!exposed)return -1;
  event("accepted","sched.control","pid0",0,0,"boost-and-restore-verified;loop-outcome-separate");
 }else error=errno;'''
assert s.count(a)==1;s=s.replace(a,z)
s=s.replace(' event("complete","runnable.loop","CLOCK_MONOTONIC",rc,error,v);\n}', ' event("complete","runnable.loop","CLOCK_MONOTONIC",rc,error,v);\n return 0;\n}')
s=s.replace(' observe();',' if(observe()){phase="finish";finish();return 0;}')
(R/'source/init.c').write_text(s)
# Only identity and exact helper admission additions in kernel.
files=['arch/arm64/kernel/asus_entry_tag.h','arch/arm64/kernel/asus_retained_trace.c']
for n in files:
 p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True)
 base=(B/'source'/n).read_text();bp=R/'source/base'/n;bp.parent.mkdir(parents=True,exist_ok=True);bp.write_text(base)
 t=base
 if n.endswith('asus_entry_tag.h'):t=t.replace('e0b1a1ba-ebd1-4454-a3fb-e8b05eedf5d9',i['kernel_uuid']).replace('profile=sparse-wdt-v1','profile=sparse-fifo-v1')
 else:
  t=t.replace('f0c3c82c-d639-4d8a-90f2-155fd4224ceb',i['helper_uuid'])
  needle='        PREFIX(" phase=observe stage=actual op=clock_gettime.final path=CLOCK_MONOTONIC rc=") ||'
  ops=[('actual',op,'pid0') for op in ['sched.original','sched.boost','sched.boost.observed','sched.restore','sched.restored']]+[('invalid','sched.control','pid0'),('accepted','sched.control','pid0'),('actual','runnable.progress','CLOCK_MONOTONIC')]
  addition=''.join('        PREFIX(" phase=observe stage='+st+' op='+op+' path='+path+' rc=") ||\n' for st,op,path in ops)
  assert t.count(needle)==1;t=t.replace(needle,addition+needle)
 p.write_text(t)
pins={};patch=''
for n in ['init.c']+files:
 a=(R/'source/base'/n).read_bytes();z=(R/'source'/n).read_bytes();pins[n]=dict(before=sha(a),after=sha(z))
 patch+=''.join(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='baseline/'+n,tofile='fifo/'+n))
(R/'source/changes.patch').write_text(patch);(R/'evidence/prepost.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(i,indent=2))
