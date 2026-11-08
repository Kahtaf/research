import json,re,hashlib
from source import ROOT,REL,fn
G=ROOT/'tests/generated';G.mkdir(exist_ok=True);pins=[]
c=(ROOT/'candidate'/REL/'mt_soc_codec_63xx.c').read_text();gpio=(ROOT/'candidate'/REL/'AudDrv_Gpio.c').read_text()
def take(s,name,origin):
 b=fn(s,name);pins.append({'source':origin,'function':name,'sha256':hashlib.sha256(b.encode()).hexdigest()});return b
# Original API adapter bodies/declarations remain byte-exact copies.
for name in ['actual-api-bodies.inc','actual-api-prototypes.inc','actual-gpio-flags.inc']:(G/name).write_bytes((ROOT/'baseline/tests/generated'/name).read_bytes())
for header in ['p00a_stock_gate.h','codec_state_controls.h']:
 data=(ROOT/'candidate'/REL/header).read_text();(G/header.replace('.h','.inc')).write_text('\n'.join(l for l in data.splitlines() if not l.startswith('#include '))+'\n');pins.append({'source':'candidate/'+str(REL/header),'sha256':hashlib.sha256(data.encode()).hexdigest(),'transformation':'kernel include directives only removed'})
names=['Ext_Speaker_Amp_Change','SavePowerState','RestorePowerState','SetAnalogSuspend_locked','SetAnalogSuspend','OpenAnalogHeadphone_locked','OpenAnalogHeadphone','UpdateHeadsetGain_locked','UpdateHeadsetGainLocked','UpdateHeadsetGain','SetMicPGAGain','ADC_LOOP_DAC_Off','Ext_Speaker_Amp_Get','Ext_Speaker_Amp_Set','Speaker_Amp_Get','Speaker_Amp_Set','mt6323_codec_add_controls','mt6323_codec_probe_locked','mt6323_codec_probe','mt6323_codec_remove','mtk_mt6323_codec_dev_probe','mtk_mt6323_codec_dev_remove','mtk_mt6323_codec_dev_shutdown','mtk_mt6323_codec_init']
parts=[]
# Gain helper precedes actual update function; untouched production arithmetic.
parts.append(take(c,'HeadsetGainReg','candidate/'+str(REL/'mt_soc_codec_63xx.c')))
for name in names:parts.append(take(c,name,'candidate/'+str(REL/'mt_soc_codec_63xx.c')))
parts += ['CODEC_STATE_CONTROL('+n+')\n' for n in ['Ext_Speaker_Amp_Get','Ext_Speaker_Amp_Set','Speaker_Amp_Get','Speaker_Amp_Set']]
(G/'actual-codec-bodies.inc').write_text('\n'.join(parts))
parts=[]
for n in ['AudDrv_GPIO_EXTAMP_Set','AudDrv_GPIO_Amp_Apply','AudDrv_GPIO_EXTHPAMP_Select','AudDrv_GPIO_Headset_Changed','AudDrv_GPIO_Headset_Boost']:parts.append(take(gpio,n,'candidate/'+str(REL/'AudDrv_Gpio.c')))
(G/'actual-gpio-bodies.inc').write_text('\n'.join(parts))
r=(ROOT/'candidate'/REL/'mt_soc_pcm_routing.c').read_text();a=(ROOT/'inputs/api'/REL/'mt_soc_afe_control.c').read_text()
(G/'actual-routing-pm.inc').write_text(take(a,'ConditionEnterSuspend','inputs/api/'+str(REL/'mt_soc_afe_control.c'))+'\n'+take(r,'mtk_routing_pm_ops_suspend','candidate/'+str(REL/'mt_soc_pcm_routing.c'))+'\n'+take(r,'mtk_routing_pm_ops_resume','candidate/'+str(REL/'mt_soc_pcm_routing.c')))
# Reuse original fixture services/scenarios, adding real mutexes and fresh regressions.
s=(ROOT/'inputs/prior/tests/contract.c').read_text();s=s.replace('int main(void){','static int original_main(void){')
s=s.replace('#include <errno.h>','#include <errno.h>\n#include <pthread.h>\n#include <time.h>\n#include <unistd.h>')
s=s.replace('#define pr_debug(...) ((void)0)','#define pr_debug(...) debug_point(__func__)\nstatic void debug_point(const char *fn);')
a=s.index('#define DEFINE_MUTEX(n)');b=s.index('typedef int32_t int32;',a)
s=s[:a]+'''static int assertions,cases,logs;
#define CHECK(x) do{__sync_fetch_and_add(&assertions,1);if(!(x)){fprintf(stderr,"FAIL line %d: %s\\n",__LINE__,#x);exit(1);}}while(0)
struct mutex {pthread_mutex_t raw;};
#define DEFINE_MUTEX(n) struct mutex n = {PTHREAD_MUTEX_INITIALIZER}
static __thread struct mutex *held[16];static __thread int depth;
static int locks;
static void fixture_lock(struct mutex *m){int i;for(i=0;i<depth;i++)CHECK(held[i]!=m);CHECK(depth<16);CHECK(!pthread_mutex_lock(&m->raw));held[depth++]=m;__sync_fetch_and_add(&locks,1);}
static void fixture_unlock(struct mutex *m){CHECK(depth>0&&held[depth-1]==m);depth--;__sync_fetch_and_sub(&locks,1);CHECK(!pthread_mutex_unlock(&m->raw));}
static int owns(struct mutex *m){int i;for(i=0;i<depth;i++)if(held[i]==m)return 1;return 0;}
#define mutex_lock(m) fixture_lock(m)
#define mutex_unlock(m) fixture_unlock(m)
#define lockdep_assert_held(m) CHECK(owns(m))
DEFINE_MUTEX(mt8163_codec_state_mutex);
static DEFINE_MUTEX(codec_registration_mutex);
static DEFINE_MUTEX(aud_amp_mutex);
static pthread_rwlock_t controls_rwsem=PTHREAD_RWLOCK_INITIALIZER;
static void registration_point(void);
static bool aud_amp_headset_switch,aud_amp_headset,aud_extamp_on,aud_hpamp_on;
static unsigned int reg_writes,allocations,frees;
static void phase_point(const char *name);
'''+s[b:]
s=s.replace('static bool mInitCodec,mAnaSuspend;','static bool mInitCodec,mAnaSuspend,mAnalogSuspendApplied;')
s=s.replace('static char events[512];','static pthread_mutex_t event_mutex=PTHREAD_MUTEX_INITIALIZER;\nstatic char events[65536];')
s=s.replace('static void ev(char c){CHECK(event_count<500);events[event_count++]=c;events[event_count]=0;}','static void ev(char c){pthread_mutex_lock(&event_mutex);CHECK(event_count<65530);events[event_count++]=c;events[event_count]=0;pthread_mutex_unlock(&event_mutex);}')
s=s.replace('#include "generated/actual-gate.inc"','#include "generated/p00a_stock_gate.inc"\n#include "generated/codec_state_controls.inc"')
s=s.replace('static void Ana_Log_Print(void){}','static void Ana_Log_Print(void){lockdep_assert_held(&mt8163_codec_state_mutex);phase_point("pm");}')
s=s.replace('static void Audio_Amp_Change(int c,bool on){(void)c;(void)on;}','static void Audio_Amp_Change(int c,bool on){(void)c;(void)on;lockdep_assert_held(&mt8163_codec_state_mutex);CHECK(mCodec_data&&mInitCodec);phase_point("headphone");UpdateHeadsetGain_locked();}')
s=s.replace('static void *kzalloc(size_t n,int flags){(void)flags;return alloc_error?NULL:calloc(1,n);}','static void *kzalloc(size_t n,int flags){(void)flags;lockdep_assert_held(&mt8163_codec_state_mutex);if(alloc_error)return NULL;__sync_fetch_and_add(&allocations,1);return calloc(1,n);}')
s=s.replace('static void kfree(void *p){free(p);}','static void kfree(void *p){lockdep_assert_held(&mt8163_codec_state_mutex);__sync_fetch_and_add(&frees,1);free(p);}')
s=s.replace('static void snd_soc_add_codec_controls(void *c,void *w,size_t n){(void)c;(void)w;(void)n;}', 'static void snd_soc_add_codec_controls(void *c,void *w,size_t n){(void)c;(void)w;(void)n;CHECK(!owns(&mt8163_codec_state_mutex));registration_point();CHECK(!pthread_rwlock_wrlock(&controls_rwsem));CHECK(!pthread_rwlock_unlock(&controls_rwsem));}')
s=s.replace('static void InitCodecDefault(void){}','static void InitCodecDefault(void){lockdep_assert_held(&mt8163_codec_state_mutex);phase_point("init");}')
s=s.replace('static void snd_soc_codec_set_drvdata(struct snd_soc_codec *c,void *d){c->driver_data=d;}','static void snd_soc_codec_set_drvdata(struct snd_soc_codec *c,void *d){c->driver_data=d;}')
s=s.replace('#include "generated/actual-codec-bodies.inc"','''#define AUDTOP_CON0 0
#define AUDTOP_CON1 1
#define AUDTOP_CON5 5
#define HEADSET_GAIN_BOOST_DB 12
#define clamp(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
static bool AudDrv_GPIO_Headset_Boost(void);
static void UpdateHeadsetGain_locked(void);
static void Ana_Set_Reg(int reg,int value,int mask){(void)reg;(void)value;(void)mask;lockdep_assert_held(&mt8163_codec_state_mutex);CHECK(mCodec_data&&mInitCodec);reg_writes++;phase_point("gain");}
#include "generated/actual-codec-bodies.inc"''')
# The analog audio stub needs the locked function declaration before its definition.
s=s.replace('static void Audio_Amp_Change(int c,bool on)', 'static void UpdateHeadsetGain_locked(void);\nstatic void Audio_Amp_Change(int c,bool on)',1)
s=s.replace('#include "generated/actual-gpio24-backend.inc"','''static int AudDrv_GPIO_EXTHPAMP_Set(int enabled){(void)enabled;return 0;}
#include "generated/actual-gpio-bodies.inc"
static bool AudDrvSuspendStatus,mFMEnable,mOffloadEnable;
static bool get_voice_status(void){return false;}
static void AudDrv_Suspend_Clk_Off(void){}
static void AudDrv_Suspend_Clk_On(void){}
#include "generated/actual-routing-pm.inc"''')
s=s.replace('Ext_Speaker_Amp_Set(NULL,&v)','Ext_Speaker_Amp_Set_state(NULL,&v)').replace('Ext_Speaker_Amp_Get(NULL,&v)','Ext_Speaker_Amp_Get_state(NULL,&v)')
s=s.replace('ADC_LOOP_DAC_Off();','mutex_lock(&mt8163_codec_state_mutex);ADC_LOOP_DAC_Off();mutex_unlock(&mt8163_codec_state_mutex);')
s=s.replace('mAnaSuspend=false;cases++;','mAnaSuspend=false;mAnalogSuspendApplied=false;AudDrvSuspendStatus=false;cases++;')
s=s.replace('CHECK(original_main()==0);','CHECK(original_main()==0);')
(ROOT/'tests/contract.c').write_text(s+'\n#include "lifecycle.c"\n')
(ROOT/'evidence/production-extraction.json').write_text(json.dumps(pins,indent=2)+'\n')
print('Extracted',len(pins),'actual production bodies/headers; generated corrected fixture')
