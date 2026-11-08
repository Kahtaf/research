from pathlib import Path
import json,subprocess,sys
import decode_switch as d
R=Path(__file__).resolve().parents[1];E=R/'evidence';T=E/'host-controls';T.mkdir(exist_ok=True)
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();a=s.index('static void cap_hex(');z=s.index('\n/* The latch',a);hexcode=s[a:z]
inc=(R/'source/switch_capture.inc').read_text();asm='asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));';assert inc.count(asm)==1;inc=inc.replace(asm,'raw = 1000 + sw_total;')
pre=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef uint64_t u64;typedef uint32_t u32;
#define __init
#define READ_ONCE(x) (x)
#define WRITE_ONCE(x,v) ((x)=(v))
#define smp_load_acquire(x) (*(x))
#define BUILD_BUG_ON(x) _Static_assert(!(x),"bounds")
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min_t(t,a,b) ((t)(a)<(t)(b)?(t)(a):(t)(b))
#define U64_MAX UINT64_MAX
#define TASK_COMM_LEN 16
unsigned int nr_cpu_ids=1;u64 cap_serial=42;int irqoff=1;
struct task_struct {int pid,prio;unsigned int policy;char comm[16];};
struct task_struct next,*current=&next;
unsigned int raw_smp_processor_id(void){return 0;}
int irqs_disabled(void){return irqoff;}
int in_interrupt(void){return 0;}
unsigned int preempt_count(void){return 2;}
void __clean_dcache_area_poc(void *a,unsigned int n){}
'''
main=r'''
int main(int argc,char **argv){
 static char area[SW_SIZE] __attribute__((aligned(64)));
 struct task_struct prev={.pid=2,.prio=120};unsigned int i,n=atoi(argv[1]);
 sw_init(area);sw_area=area;
 for(i=1;i<=n;i++){
  prev.pid=i==2?1:2;next.pid=i==3?1:10+i;next.prio=120;next.policy=0;
  memset(next.comm,0,16);memcpy(next.comm,"worker",6);
  asus_capture_switch(&prev,i==2?1:0);
 }
 if(argc>2 && !strcmp(argv[2],"guard")){area[330]^=1;asus_capture_switch(&prev,0);}
 if(argc>2 && !strcmp(argv[2],"admission")){irqoff=0;asus_capture_switch(&prev,0);}
 if(argc>2 && !strcmp(argv[2],"busy")){sw_busy=true;asus_capture_switch(&prev,0);}
 fwrite(area,1,SW_SIZE,stdout);return 0;
}
'''
(T/'writer.c').write_text(pre+hexcode+inc+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'writer.c'),'-o',str(T/'writer')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
def legacy():
 a=bytearray(b' '*5952);tag=('A49CAP1 uuid='+d.UUID+' rows=15 row=384 fields=17 header=192').encode();a[:len(tag)]=tag;a[127]=10;a[128:138]=b'A49FAULT 0';a[191]=10
 for row in range(15):
  line=bytearray(b' '*384);line[:9]=('VA49C %02x '%row).encode();f=[1,row//3,row%3]+[0]*14
  for i,v in enumerate(f):line[9+i*17:25+i*17]=('%016x'%v).encode()
  line[352:368]=b'0000000000000001';line[-1]=10;a[192+row*384:192+(row+1)*384]=line
 return bytes(a)
base=legacy();results={}
for name,n,arg,expect in [('empty',0,None,'UNKNOWN'),('positive',3,None,'FINITE_SWITCH_CAPTURE'),('wrap',12,None,'FINITE_SWITCH_CAPTURE'),('guard',3,'guard','UNKNOWN'),('admission',3,'admission','UNKNOWN'),('busy',3,'busy','UNKNOWN')]:
 sw=subprocess.check_output([str(T/'writer'),str(n)]+([arg] if arg else []));data=base+sw;out=d.decode(data);assert out['status']==expect,(name,out)
 if name=='wrap':assert out['bounds']['first_retained']==5 and out['last_PID1_out']['sequence']==2 and out['last_PID1_in']['sequence']==3
 if name=='positive':
  for variant,pos in [('invalid',384),('tail',384+232),('metadata',64+160)]:
   t=bytearray(sw);t[pos]^=1;o=d.decode(base+t);assert o['status']=='UNKNOWN',(variant,o);results['torn_'+variant]=o['reason']
 results[name]=dict(status=out['status'],reason=out.get('reason'),bounds=out.get('bounds'))
 (T/(name+'.bin')).write_bytes(data)
(T/'writer').unlink()
(E/'encoding-controls.json').write_text(json.dumps(dict(status='PASS',actual_source_extracted=True,host_only_substitution='CNTVCT asm replaced with deterministic raw value; kernel environment stubs',controls=results),indent=2)+'\n')
print(json.dumps(results,indent=2))
