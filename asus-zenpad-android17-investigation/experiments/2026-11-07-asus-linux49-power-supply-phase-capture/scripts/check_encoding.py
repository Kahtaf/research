from pathlib import Path
import json,subprocess,re
import decode_power as d
R=Path(__file__).resolve().parents[1];E=R/'evidence';T=E/'host-controls';T.mkdir(exist_ok=True)
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text()
hexcode=s[s.index('static void cap_hex('):s.index('\n/* The latch')]
code=s[s.index('/* Independent scheduler capture:'):s.index('static void __init cap_init(')]
asm='asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));';assert code.count(asm)==3;code=code.replace(asm,'raw = ++ticks;')
interface=(R/'source/ps-interface.inc').read_text().split('#ifdef')[0]
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
int fake_irq=0,taskcontext=1,busy=0,hardirq=0;unsigned int cpuid=0,nr_cpu_ids=1,pc=0;u64 cap_serial=42,ticks=1000;
#define raw_spin_trylock_irqsave(lock,flags) ((flags)=fake_irq, busy?0:(fake_irq=1,*(lock)=1,1))
#define raw_spin_unlock_irqrestore(lock,flags) (*(lock)=0,fake_irq=(flags))
struct task_struct {int pid,prio;unsigned int policy,flags;char comm[16];};
struct task_struct task,*current=&task;
unsigned int raw_smp_processor_id(void){return cpuid;}
int irqs_disabled(void){return fake_irq;}
int in_interrupt(void){return !taskcontext;}
int in_task(void){return taskcontext;}
int in_nmi(void){return 0;}
int in_irq(void){return hardirq;}
int in_serving_softirq(void){return 0;}
unsigned int preempt_count(void){return pc;}
void __clean_dcache_area_poc(void *a,unsigned int n){}
'''
fn=int(json.loads((E/'linked-capture.json').read_text())['symbols']['power_supply_changed_work']['address'],16)
main=r'''
#define PSY 0xffffffc012340000ULL
#define WORK (PSY+0x2e0)
#define CONSUMER 0xffffffc012350000ULL
#define CALLBACK 0xffffff8008123400ULL
static void selectpid(int pid){
 struct task_struct prev=task;task.pid=pid;task.prio=120;task.policy=0;task.flags=PF_WQ_WORKER;
 memset(task.comm,0,16);memcpy(task.comm,pid==119?"kworker/0:3":"kworker/0:1",11);
 fake_irq=1;pc=2;asus_capture_switch(&prev,0,0,0,3);pc=0;fake_irq=0;
}
static void step(struct asus_ps_capture *c,unsigned int code){asus_capture_ps_step(c,code,code==3?1:0,(code==7||code==11||code==13)?0:U64_MAX);if(fake_irq||ps_lock)exit(81);}
int main(int argc,char **argv){
 static char area[SW_SIZE+WD_SIZE+PS_SIZE] __attribute__((aligned(64)));
 struct asus_ps_capture body,p,q,ext;u64 token;int k;
 sw_init(area);wd_init(area+SW_SIZE);ps_init(area+SW_SIZE+WD_SIZE);
 sw_area=area;wd_area=area+SW_SIZE;ps_area=area+SW_SIZE+WD_SIZE;task.pid=1;
 selectpid(119);token=asus_capture_work_enter(FUNCTION,WORK);
 asus_capture_ps_begin(&body,1,WORK,PSY,"battery",0,1,0,NULL);
 for(k=2;k<=6;k++)step(&body,k);
 asus_capture_ps_begin(&ext,50,0,CONSUMER,"b",CALLBACK,0,PSY,"battery");
 asus_capture_ps_begin(&p,40,0,CONSUMER,"b",CALLBACK,0,0,NULL);
 asus_capture_ps_begin(&q,40,0,CONSUMER,"b",CALLBACK,2,0,NULL);
 asus_capture_ps_step(&q,41,2,(u32)-61);asus_capture_ps_step(&p,41,0,0);asus_capture_ps_step(&ext,51,0,U64_MAX);
 if(!strcmp(argv[1],"nested"))goto done;
 for(k=7;k<=12;k++)step(&body,k);
 pc=1;fake_irq=1; /* legitimate task atomic/IRQoff context */
 asus_capture_ps_begin(&p,40,0,PSY,"battery",CALLBACK,12,0,NULL);
 if(!strcmp(argv[1],"missing")){fake_irq=0;pc=0;goto done;}
 if(!strcmp(argv[1],"interleave")){
  pc=0;fake_irq=0;selectpid(42);
  asus_capture_ps_begin(&q,40,0,CONSUMER,"other",CALLBACK,3,0,NULL);asus_capture_ps_step(&q,41,3,0);
  selectpid(119);pc=1;fake_irq=1;
 }
 asus_capture_ps_step(&p,41,12,0);pc=0;fake_irq=0;
 if(!strcmp(argv[1],"irq")){
  pc=0x10000;hardirq=1;taskcontext=0;fake_irq=1;
  asus_capture_ps_begin(&q,40,0,PSY,"battery",CALLBACK,0,0,NULL);asus_capture_ps_step(&q,41,0,0);
  pc=0;hardirq=0;taskcontext=1;fake_irq=0;goto done;
 }
 if(!strcmp(argv[1],"busy")){busy=1;asus_capture_ps_begin(&q,40,0,PSY,"battery",CALLBACK,0,0,NULL);busy=0;goto done;}
 if(!strcmp(argv[1],"interleave"))goto done;
 for(k=13;k<=20;k++)step(&body,k);
 asus_capture_work_return(token);
 done:if(fake_irq||ps_lock||wd_lock)return 82;
 fwrite(area,1,sizeof(area),stdout);return 0;
}
'''.replace('FUNCTION',hex(fn)+'ULL')
(T/'writer.c').write_text(pre+interface+hexcode+code+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'writer.c'),'-o',str(T/'writer')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
def legacy():
 a=bytearray(b' '*5952);tag=('A49CAP1 uuid='+d.UUID+' rows=15 row=384 fields=17 header=192').encode();a[:len(tag)]=tag;a[127]=10;a[128:138]=b'A49FAULT 0';a[191]=10
 for row in range(15):
  line=bytearray(b' '*384);line[:9]=('VA49C %02x '%row).encode();f=[1,row//3,row%3]+[0]*14
  if row==0:f[3]=f[4]=42<<8;f[5]=f[6]=1;f[10]=4
  for i,v in enumerate(f):line[9+i*17:25+i*17]=('%016x'%v).encode()
  line[352:368]=b'0000000000000001';line[-1]=10;a[192+row*384:192+(row+1)*384]=line
 return bytes(a)
results={};fixtures={}
for mode in ['positive','nested','missing','interleave','irq','busy']:
 data=legacy()+subprocess.check_output([str(T/'writer'),mode]);fixtures[mode]=data;out=d.decode(data)
 expect='UNKNOWN' if mode=='busy' else 'FINITE_POWER_CAPTURE';assert out['status']==expect,(mode,out)
 if mode=='positive':
  assert out['target']['code']==20 and out['target']['actual_WQ_postcall_recorded'] is True
  assert out['target']['property']['status']=='JOINED_LOCAL_PAIR' and out['target']['property']['returned']
  assert any(p['status']=='UNKNOWN_ENTRY_OUTSIDE_HORIZON' for p in out['pairs'])
 if mode=='nested':
  assert [p['status'] for p in out['pairs']]==['PAIRED_RETURN']*3
  assert out['target']['property']['status']=='JOINED_LOCAL_PAIR' and out['snapshots']['external']['name_hex']=='62'+'00'*15
 if mode=='missing':
  assert out['target']['code']==12 and out['target']['property']['status']=='JOINED_LOCAL_PAIR' and not out['target']['property']['returned']
  assert out['snapshots']['property']['preempt']==1 and out['snapshots']['property']['context']==15
 if mode=='interleave':
  assert out['target']['status']=='UNKNOWN'
  pairs=out['pairs'];assert any(p['body_token']==0 and p['supply']=='other' for p in pairs)
  assert out['snapshots']['property']['body_token']==out['snapshots']['body']['token']
 if mode=='irq':assert out['target']['property']['status']=='UNKNOWN' and out['snapshots']['property']['body_token']==0
 (T/(mode+'.bin')).write_bytes(data);(T/(mode+'-decoded.json')).write_text(json.dumps(out,indent=2)+'\n')
 results[mode]=dict(status=out['status'],target=out['target'],bounds=out.get('bounds'),reason=out.get('reason'))
# A few targeted negative encodings, not a broad matrix.
for mode,pos in [('torn_snapshot',d.BASE+d.OFFSET+8*d.ROW+424),('torn_metadata',d.BASE+64+160),('guard',d.BASE+320),('enum',d.BASE+d.OFFSET+9*d.ROW+9+8*17)]:
 t=bytearray(fixtures['missing']);t[pos]=ord('f') if mode=='enum' else t[pos]^1;out=d.decode(t)
 assert out['status']=='UNKNOWN',(mode,out);results[mode]=dict(status=out['status'],reason=out.get('reason'))
(T/'writer').unlink()
(E/'encoding-controls.json').write_text(json.dumps(dict(status='PASS',actual_source_extracted=True,host_only_substitutions='Kernel primitives stubbed; only three raw CNTVCT samples replaced by deterministic increments; no target evidence.',controls=results),indent=2)+'\n')
print(json.dumps({k:v['status'] for k,v in results.items()},indent=2))
