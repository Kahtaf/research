"""One finite host scenario compares the real base and instrumented driver bodies."""
from pathlib import Path
import subprocess,json,re
R=Path(__file__).resolve().parents[1];T=R/'evidence/host-semantics';T.mkdir(exist_ok=True);P='drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc'
def source(p,prefix=''):
 s=p.read_text().split('#ifdef CONFIG_ASUS_P00A_MAIN_BATTERY_SOC')[0];s=re.sub(r'^#include[^\n]*\n','',s,flags=re.M)
 for name in ['p00a_pmic_result','p00a_pmic_prepare_adc','asus_p00a_pmic_present','asus_p00a_pmic_adc']:s=re.sub(r'\b'+name+r'\b',prefix+name,s)
 return s
pre=r'''
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
typedef uint32_t u32;typedef uint64_t u64;
#define BIT(x) (1U<<(x))
#define READ_ONCE(x) (x)
#define ADC_COUNT_TIMEOUT 100
#define AUXADC_ADC2 102
#define AUXADC_ADC3 103
#define AUXADC_ADC1 101
#define AUXADC_ADC0 100
#define AUXADC_CON19 119
#define AUXADC_ADC19 219
#define AUXADC_CON11 111
#define AUXADC_CON22 122
#define CHR_CON7 7
#define PMIC_RG_ADC_DECI_GDLY_MASK 3
#define PMIC_RG_ADC_DECI_GDLY_SHIFT 14
#define PMIC_RG_VBUF_EN_MASK 1
#define PMIC_RG_VBUF_EN_SHIFT 4
#define PMIC_RG_BATON_EN_SHIFT 0
#define PMIC_BATON_TDET_EN_SHIFT 2
#define PMIC_RGS_BATON_UNDET_SHIFT 12
static int pmic_adc_lock,pmic_adc_mutex,pmicAuxadc_irq_lock=1,pwrap_regmap=1;
static int irq,spin,mutex,awake,reads,delayreads,pollreads,events[256],count;
static void event(int e){if(count>=256)abort();events[count++]=e;}
#define spin_lock_irqsave(p,f) do {event(1);if(spin)abort();(f)=irq;irq=1;spin=1;} while(0)
#define spin_unlock_irqrestore(p,f) do {event(2);if(!spin)abort();spin=0;irq=(f);} while(0)
static void mutex_lock(int*p){event(3);if(mutex)abort();mutex=1;}
static void mutex_unlock(int*p){event(4);if(!mutex)abort();mutex=0;}
static void __pm_stay_awake(int p){event(5);awake=1;}
static void __pm_relax(int p){event(6);awake=0;}
static int pmic_read_interface_nolock(unsigned r,unsigned*v,unsigned mask,unsigned shift){
 event(r==AUXADC_CON19?7:8);reads++;if(!spin||!irq||!mutex)abort();
 *v=r==AUXADC_CON19?(delayreads++==0):0;return 0;
}
static int pmic_config_interface_nolock(unsigned r,unsigned v,unsigned mask,unsigned shift){event(9);if(!spin||!irq)abort();return 0;}
static int pmic_read_interface(unsigned r,unsigned*v,unsigned mask,unsigned shift){
 event(r==CHR_CON7?10:11);reads++;
 if(r==CHR_CON7)*v=5;else{if(!mutex||!awake||spin)abort();*v=++pollreads%2?0:BIT(15)|6000;}return 0;
}
static int pmic_config_interface(unsigned r,unsigned v,unsigned mask,unsigned shift){event(r==AUXADC_CON11?12:(v?14:13));if(!mutex||!awake||spin)abort();return 0;}
static void usleep_range(int a,int z){event(15);if(spin||irq||a!=1000||z!=2000)abort();}
static void udelay(int us){event(16);if(spin||irq||us!=300)abort();}
'''
interface=(R/'source/pmic-interface.inc').read_text().split('#ifdef')[0]
hooks=r'''
static unsigned nexttoken,seen[80];
void asus_capture_pmic_begin(struct asus_pmic_capture*c,const struct asus_pmic_capture*p,unsigned code,u32 ch,u32 samples,unsigned long caller){
 memset(c,0,sizeof(*c));c->token=++nexttoken;c->parent=p?p->token:0;seen[code]++;
}
void asus_capture_pmic_step(struct asus_pmic_capture*c,unsigned code,int sample,int poll,u32 status){seen[code]++;}
'''
main=r'''
int main(void){
 int present1,present2,mv1,mv2,ret1,ret2,expected[256],expected_count,expected_reads;
 ret1=orig_asus_p00a_pmic_present(&present1);if(ret1||spin||mutex||irq)abort();
 ret1=orig_asus_p00a_pmic_adc(6,5,&mv1);if(ret1||spin||mutex||irq||awake)abort();
 expected_count=count;memcpy(expected,events,sizeof(events));expected_reads=reads;
 count=reads=delayreads=pollreads=0;
 ret2=asus_p00a_pmic_present(&present2);if(ret2||spin||mutex||irq)abort();
 ret2=asus_p00a_pmic_adc(6,5,&mv2);if(ret2||spin||mutex||irq||awake)abort();
 if(ret1!=ret2||present1!=present2||mv1!=mv2||count!=expected_count||reads!=expected_reads||memcmp(expected,events,count*sizeof(int)))abort();
 if(seen[4]!=1||seen[5]!=1||seen[26]!=1||seen[27]!=1||seen[28]!=1||seen[29]!=1||seen[38]!=5||seen[39]!=5||seen[40]!=10||seen[41]!=10||seen[44]!=5||seen[45]!=5||seen[61]!=2||seen[62]!=2||seen[63]!=2||seen[64]!=2||seen[65]!=1||seen[66]!=1||seen[67]!=1||seen[68]!=1||seen[69]!=2||seen[70]!=2||seen[74]!=1||seen[75]!=1||seen[59]!=1||seen[79]!=1)abort();
 puts("PASS: base/candidate primitive sequence, counts, outputs, int status and final lock/IRQ state agree; one 5-sample voltage scenario exercises prepare busy/config + sleeps and every per-sample poll");return 0;
}
'''
(T/'scenario.c').write_text(pre+interface+hooks+source(R/'source/base'/P,'orig_')+source(R/'source'/P)+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Wno-unused-variable',str(T/'scenario.c'),'-o',str(T/'scenario')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode();q=subprocess.run([str(T/'scenario')],capture_output=True,text=True);(T/'result.txt').write_text(q.stdout+q.stderr);q.check_returncode();(T/'scenario').unlink()
(R/'evidence/semantics-control.json').write_text(json.dumps(dict(status='PASS',actual_driver_sources=True,scenarios=1,hardware_access=False,comparison='Original primitive event order/counts, return status, synthetic output equality only in memory, final lock/IRQ/wake state; all new argument values limited to status/channel/indices. No raw outputs emitted.',stdout=q.stdout),indent=2)+'\n');print(q.stdout,end='')
