"""Three focused groups: actual fixed writers, refusal/overflow, primitive order."""
from pathlib import Path
import ast,json,subprocess,re
R=Path(__file__).resolve().parents[1];T=R/'evidence/controls';T.mkdir(exist_ok=True)
p=R.parent/'2026-11-07-asus-linux49-power-supply-phase-capture/scripts/check_encoding.py';tree=ast.parse(p.read_text());pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='pre' for t in n.targets))
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();hexcode=s[s.index('static void cap_hex('):s.index('\n/* The latch')];code=s[s.index('/* Independent scheduler capture:'):s.index('static void __init cap_init(')]
assert code.count('asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));')==4
code=code.replace('asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));','raw = ++ticks;').replace('(unsigned long)__builtin_return_address(0)','0xffffff8008100020UL')
interface=(R.parent/'2026-11-07-asus-linux49-power-supply-phase-capture/source/ps-interface.inc').read_text().split('#ifdef')[0]+(R.parent/'2026-11-08-asus-linux49-pmic-stage-capture/source/pmic-interface.inc').read_text().split('#ifdef')[0]
pre+='\n#define asus_p00a_battery_get_property ((void*)0xffffff8008200000UL)\n#define asus_p00a_pmic_adc ((void*)0xffffff8008300000UL)\n#define __const_udelay ((void*)0xffffff8008100000UL)\n'
main=r'''
static void check(int ok){if(!ok)exit(81);}
int main(int argc,char **argv){
 static char area[SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE+DL_SIZE] __attribute__((aligned(64)));
 struct asus_ps_capture b,p; struct asus_pmic_capture a;
 unsigned long cr=(unsigned long)asus_p00a_pmic_adc+928;
 u64 g;int j;
 sw_init(area);wd_init(area+SW_SIZE);ps_init(area+SW_SIZE+WD_SIZE);pm_init(area+SW_SIZE+WD_SIZE+PS_SIZE);dl_init(area+SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE);
 sw_area=area;wd_area=area+SW_SIZE;ps_area=area+SW_SIZE+WD_SIZE;pm_area=area+SW_SIZE+WD_SIZE+PS_SIZE;dl_area=area+SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE;
 task.pid=73;
 asus_capture_ps_begin(&b,1,0xffffff8008900000UL,0xffffff8008910000UL,"battery",0,1,0,NULL);
 asus_capture_ps_step(&b,12,0,0);
 asus_capture_ps_begin(&p,40,0,0xffffff8008910000UL,"battery",0xffffff8008800000UL,66,0,NULL);
 asus_capture_pmic_begin(&a,NULL,20,6,5,(unsigned long)asus_p00a_battery_get_property+468);
 if(!strcmp(argv[1],"overflow"))dl_gen=U64_MAX;
 for(j=0;j<5;j++){
  pm_record(&a,38,j,-1,0x80000000U,false,(unsigned long)asus_p00a_pmic_adc+912);
  if(!strcmp(argv[1],"overflow")){check(dl_storage[256+47]=='1');break;}
  check(dl_gen==(u64)j+1&&dl_state==1&&dl_read_domain==0);
  task.pid=74;asus_capture_delay_calc(1288500,52000,250,16750312500000UL,3900,cr);check(dl_state==1);task.pid=73;
  taskcontext=0;hardirq=1;asus_capture_delay_calc(1288500,52000,250,16750312500000UL,3900,cr);check(dl_state==1);taskcontext=1;hardirq=0;
  asus_capture_delay_calc(1288500,52000,250,16750312500000UL,3900,cr+4);check(dl_state==1);
  if(!strcmp(argv[1],"overlap")){pm_record(&a,38,j,-1,0x80000000U,false,(unsigned long)asus_p00a_pmic_adc+912);check(dl_storage[256+24]=='1');break;}
  asus_capture_delay_calc(1288500,52000,250,16750312500000UL,3900,cr);check(dl_state==2);
  task.pid=74;check(!asus_capture_delay_begin(3900,0xffffff8008100030UL));check(dl_state==2);task.pid=73;
  g=asus_capture_delay_begin(3900,0xffffff8008100030UL);check(g==dl_gen&&dl_state==3&&dl_read_domain==1);
  if(!strcmp(argv[1],"wrongbackend")){dl_read_domain=0;asus_capture_delay_point(g,0,0,0,3900);check(dl_storage[256+36]=='1');break;}
  asus_capture_delay_point(g,0,0,0,3900);asus_capture_delay_point(g,1,0,100,3900);
  asus_capture_delay_point(g,2,1,100,3900);asus_capture_delay_point(g,3,256,120,3900);
  asus_capture_delay_point(g,4,65536,150,3900);asus_capture_delay_point(g,5,1048576,180,3900);
  asus_capture_delay_point(g,6,1048577,4000,3900);check(dl_state==4);
  pm_record(&a,39,j,-1,0x80000000U,false,0);check(dl_state==5);
 }
 check(!fake_irq&&!pm_lock&&!dl_lock);fwrite(dl_storage,1,DL_SIZE,stdout);return 0;
}
'''
(T/'writer.c').write_text(pre+interface+hexcode+code+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'writer.c'),'-o',str(T/'writer')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
results={}
for mode in ['latest','overlap','overflow','wrongbackend']:
 b=subprocess.check_output([str(T/'writer'),mode]);assert len(b)==2560;(T/(mode+'.bin')).write_bytes(b);results[mode]=dict(passed=True,bytes=len(b))
assert (T/'latest.bin').read_bytes()[256:320]==b'A49DLOSS 0 guard=0 busy=0 admission=0 overflow=0'.ljust(63)+b'\n'
# Actual helper and delay bodies; only hardware primitives/hooks are host stubs.
base=(R/'source/base/arch/arm64/lib/delay.c').read_text();cand=(R/'source/arch/arm64/lib/delay.c').read_text()
def body(s):return s[s.index('void __delay('):s.index('EXPORT_SYMBOL(__delay);')]
helper=cand[cand.index('static __always_inline cycles_t selected_delay_counter'):cand.index('void __delay(')]
helper=helper.replace('asm volatile("mrs %0, cntpct_el0" : "=r" (counter));','counter = physical_read();')
preamble=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint64_t u64;typedef unsigned long cycles_t;
#define U64_MAX UINT64_MAX
#define __always_inline inline __attribute__((always_inline))
static unsigned long reads,physical,virtual,ool,barriers,relaxes,stages,selected,key;
static void isb(void){barriers++;}
static cycles_t next(void){return 100+(reads++)*1000;}
static cycles_t physical_read(void){physical++;return next();}
static cycles_t get_cycles(void){isb();virtual++;if(key)ool++;return next();}
static void cpu_relax(void){relaxes++;}
static u64 asus_capture_delay_begin(unsigned long c,unsigned long p){return selected;}
static void asus_capture_delay_point(u64 g,unsigned int s,u64 i,unsigned long v,unsigned long c){stages|=1UL<<s;}
static void reset(void){reads=physical=virtual=ool=barriers=relaxes=stages=0;}
'''
main=r'''
int main(void){unsigned long br,bb,bx,bs;for(selected=0;selected<2;selected++)for(key=0;key<2;key++){
reset();base_delay(3900);br=reads;bb=barriers;bx=relaxes;bs=stages;
reset();candidate_delay(3900);
if(reads!=br||barriers!=bb||relaxes!=bx||stages!=bs||reads!=5||barriers!=5||relaxes!=3)abort();
if(selected?(physical!=5||virtual||ool):(physical||virtual!=5||ool!=(key?5:0)))abort();
}puts("PASS: actual selected start/all condition reads physical for both virtual keys; unselected original direct/OOL; same single ISB/read, read count, YIELD count, milestones and return condition");}
'''
(T/'primitive.c').write_text(preamble+helper+body(base).replace('__delay','base_delay')+body(cand).replace('__delay','candidate_delay')+main)
q=subprocess.run(['cc','-std=gnu11','-O2',str(T/'primitive.c'),'-o',str(T/'primitive')],capture_output=True,text=True);(T/'primitive-compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
q=subprocess.run([str(T/'primitive')],capture_output=True,text=True);q.check_returncode();(T/'primitive-result.txt').write_text(q.stdout)
results['primitive_route']=dict(passed=True,result=q.stdout.strip(),actual_bodies=True)
(T/'writer').unlink();(T/'primitive').unlink()
(R/'evidence/controls.json').write_text(json.dumps(dict(status='PASS_FOCUSED_WRITER_AND_ROUTE_CONTROLS',controls=results,synthetic_not_physical=True,substitutions='kernel publication/context/cache stubs; old raw samples deterministic; code addresses deterministic; actual helper physical instruction mocked; virtual key mock exercises both routes'),indent=2)+'\n');print(json.dumps(results,indent=2))
