from pathlib import Path
import json,subprocess
import decode_work as d
R=Path(__file__).resolve().parents[1];E=R/'evidence';T=E/'host-controls';T.mkdir(exist_ok=True)
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();hexcode=s[s.index('static void cap_hex('):s.index('\n/* The latch')]
sw=s[s.index('/* Independent scheduler capture:'):s.index('/* Independent bounded dispatch events.')]
wd=(R/'source/work_capture.inc').read_text();asm='asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));'
assert sw.count(asm)==wd.count(asm)==1;sw=sw.replace(asm,'raw = ++ticks;');wd=wd.replace(asm,'raw = ++ticks;')
pre=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef uint64_t u64;typedef uint32_t u32;
#define __init
#define noinline __attribute__((noinline))
#define READ_ONCE(x) (x)
#define WRITE_ONCE(x,v) ((x)=(v))
#define smp_load_acquire(x) (*(x))
#define BUILD_BUG_ON(x) _Static_assert(!(x),"bounds")
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min_t(t,a,b) ((t)(a)<(t)(b)?(t)(a):(t)(b))
#define U64_MAX UINT64_MAX
#define TASK_COMM_LEN 16
#define PF_WQ_WORKER 0x20
#define DEFINE_RAW_SPINLOCK(n) int n=0
int fake_irq=0,taskcontext=1,busy=0;unsigned int cpuid=0,nr_cpu_ids=1,pc=0;u64 cap_serial=42,ticks=1000;
#define raw_spin_trylock_irqsave(lock,flags) ((flags)=fake_irq, busy?0:(fake_irq=1,*(lock)=1,1))
#define raw_spin_unlock_irqrestore(lock,flags) (*(lock)=0,fake_irq=(flags))
struct task_struct {int pid,prio;unsigned int policy,flags;char comm[16];};
struct task_struct task,*current=&task;
unsigned int raw_smp_processor_id(void){return cpuid;}
int irqs_disabled(void){return fake_irq;}
int in_interrupt(void){return !taskcontext;}
int in_task(void){return taskcontext;}
int in_nmi(void){return 0;}
unsigned int preempt_count(void){return pc;}
void __clean_dcache_area_poc(void *a,unsigned int n){}
'''
main=r'''
static void selectpid(int pid){
 struct task_struct prev=task;task.pid=pid;task.prio=120;task.policy=0;task.flags=PF_WQ_WORKER;
 memset(task.comm,0,16);memcpy(task.comm,pid==119?"kworker/0:3":"kworker/0:1",11);
 fake_irq=1;pc=2;asus_capture_switch(&prev,0,0,0,3);pc=0;fake_irq=0;
}
int main(int argc,char **argv){
 static char area[SW_SIZE+WD_SIZE] __attribute__((aligned(64)));u64 a,b,t;int i;
 sw_init(area);wd_init(area+SW_SIZE);sw_area=area;wd_area=area+SW_SIZE;task.pid=1;
 if(!strcmp(argv[1],"early")){wd_area=NULL;assert_not_used:;t=asus_capture_work_enter(0x1000,0x2000);wd_area=area+SW_SIZE;asus_capture_work_return(t);goto done;}
 selectpid(119);a=asus_capture_work_enter(0xffffff8008123400ULL,0xffffffc012340000ULL);
 if(fake_irq || wd_lock)return 81;
 selectpid(42);b=asus_capture_work_enter(0xffffff8008123500ULL,0xffffffc012350000ULL);asus_capture_work_return(b);
 selectpid(119);asus_capture_work_return(a);
 if(!strcmp(argv[1],"wrap")){
  for(i=0;i<9;i++){t=asus_capture_work_enter(0xffffff8008123600ULL,0xffffffc012360000ULL);if(i<8)asus_capture_work_return(t);}
 }else{
  t=asus_capture_work_enter(0xffffff8008123600ULL,0xffffffc012360000ULL);
  if(strcmp(argv[1],"missing"))asus_capture_work_return(t);
 }
 if(!strcmp(argv[1],"busy")){busy=1;asus_capture_work_enter(0x1000,0x2000);busy=0;}
 if(!strcmp(argv[1],"guard")){area[SW_SIZE+330]^=1;asus_capture_work_enter(0x1000,0x2000);}
 if(!strcmp(argv[1],"admission")){nr_cpu_ids=2;asus_capture_work_enter(0x1000,0x2000);}
 if(!strcmp(argv[1],"overflow")){wd_total=U64_MAX-1;asus_capture_work_enter(0x1000,0x2000);}
 done:if(fake_irq || wd_lock)return 82;
 fwrite(area,1,sizeof(area),stdout);return 0;
}
'''.replace('assert_not_used:;','')
(T/'writer.c').write_text(pre+hexcode+sw+wd+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'writer.c'),'-o',str(T/'writer')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
def legacy():
 a=bytearray(b' '*5952);tag=('A49CAP1 uuid='+d.UUID+' rows=15 row=384 fields=17 header=192').encode();a[:len(tag)]=tag;a[127]=10;a[128:138]=b'A49FAULT 0';a[191]=10
 for row in range(15):
  line=bytearray(b' '*384);line[:9]=('VA49C %02x '%row).encode();f=[1,row//3,row%3]+[0]*14
  if row==0:f[3]=f[4]=42<<8;f[5]=f[6]=1;f[10]=4
  for i,v in enumerate(f):line[9+i*17:25+i*17]=('%016x'%v).encode()
  line[352:368]=b'0000000000000001';line[-1]=10;a[192+row*384:192+(row+1)*384]=line
 return bytes(a)
results={};good=None
for mode in ['positive','missing','wrap','early','busy','guard','admission','overflow']:
 data=legacy()+subprocess.check_output([str(T/'writer'),mode]);out=d.decode(data);(T/(mode+'.bin')).write_bytes(data)
 expect='FINITE_WORK_CAPTURE' if mode in ['positive','missing','wrap'] else 'UNKNOWN';assert out['status']==expect,(mode,out)
 if mode=='positive':
  assert out['target']['status']=='SELECTED_WORKER_POSTCALL_RECORDED';assert [(p['token'],p['return_sequence']) for p in out['pairs']]==[(1,4),(2,3),(3,6)];good=data
 if mode in ['missing','wrap']:assert out['target']['status']=='SELECTED_WORKER_DISPATCH_BOUNDARY_NO_POSTCALL_IN_FINITE_CAPTURE'
 if mode=='wrap':assert out['bounds']['first_retained']==6 and any(p['status']=='UNKNOWN_ENTRY_OUTSIDE_RING_HORIZON' for p in out['pairs'])
 (T/(mode+'-decoded.json')).write_text(json.dumps(out,indent=2)+'\n');results[mode]=dict(status=out['status'],reason=out.get('reason'),target=out['target'],bounds=out.get('bounds'))
# Bounded torn, identity, loss and cross-join controls.
mutations={}
for name,pos in [('invalid_marker',9600+384),('torn_row_tail',9600+384+288),('torn_header',9600+64+160),('identity',9600+20),('partial_loss',9600+256+17)]:
 t=bytearray(good);t[pos]^=1;mutations[name]=t
# Latest entry row4 token3, event5; alter both event identity and pair proof independently.
t=bytearray(good);t[9600+384+4*320+9+4*17:9600+384+4*320+25+4*17]=b'000000000000002a';mutations['crossjoin_wrong_pid']=t
t=bytearray(good);t[9600+384+5*320+9+1*17:9600+384+5*320+25+1*17]=b'0000000000000001';mutations['duplicate_pair_return']=t
for name,t in mutations.items():
 out=d.decode(t);assert out['status']=='UNKNOWN',(name,out);results[name]=dict(status=out['status'],reason=out.get('reason'))
# A different latest selected worker cannot be attributed to stale entry.
t=bytearray(good)
for slot in [2]:
 for field,val in [(4,43)]:t[5952+384+slot*320+9+field*17:5952+384+slot*320+25+field*17]=('%016x'%val).encode()
# This must fail a crossjoin, even though no raw pointer symbol is involved.
out=d.decode(t);assert out['status']=='UNKNOWN';results['stale_selected_worker']=dict(status=out['status'],reason=out.get('reason'))
(T/'writer').unlink()
(E/'encoding-controls.json').write_text(json.dumps(dict(status='PASS',actual_source_extracted=True,host_only_substitutions='kernel primitives stubbed; only CNTVCT asm replaced with deterministic raw increment; no target evidence',controls=results),indent=2)+'\n')
print(json.dumps({k:v['status'] for k,v in results.items()},indent=2))
