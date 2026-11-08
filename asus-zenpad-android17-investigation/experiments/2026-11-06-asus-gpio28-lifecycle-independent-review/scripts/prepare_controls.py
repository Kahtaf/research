"""Compile actual registrations, guarded callback bodies and boundary macro.

Unrelated callbacks/analog services are explicit sentinels. Only readiness
rejection is asserted for all callbacks; this is not analog signal emulation.
"""
import json,re
from audit import ROOT,SOURCE,REL,H,functions,masked
s=(ROOT/'tests/contract.c').read_text()
production=(SOURCE/'candidate'/REL/'mt_soc_codec_63xx.c').read_text();fs=functions(production)
names={r['callback'] for r in json.loads((ROOT/'evidence/source-audit.json').read_text())['actual_private_control_registrations']}
existing=functions((ROOT/'tests/generated/actual-codec-bodies.inc').read_text())
extra=[];receipts=[]
for n in sorted(names-existing.keys()):
    extra.append(fs[n]['text']+'CODEC_STATE_CONTROL('+n+')\n')
    receipts.append({'function':n,'source_line':fs[n]['line'],'sha256':H(fs[n]['text'].encode())})
(ROOT/'tests/generated/extra-control-bodies.inc').write_text('\n'.join(extra))
tables=re.findall(r'(static const struct snd_kcontrol_new\s+(\w+)\[\]\s*=\s*\{[\s\S]*?\n\};)',production)
raw='\n'.join(t for t,n in tables)
# Control data are genuine production arrays; the fixture supplies only macro/type layout.
(ROOT/'tests/generated/actual-control-tables.inc').write_text(raw+'\n')
all_names=set(re.findall(r'\b(\w+(?:_Get|_Set))\b',masked(raw)))
unrelated=all_names-names
stubs='\n'.join('static int '+n+'(struct snd_kcontrol *k,struct snd_ctl_elem_value *v){(void)k;(void)v;CHECK(false);return -999;}' for n in sorted(unrelated))
s=s.replace('struct {long value[4];} integer;', 'struct {long value[4];} integer;struct {unsigned int item[4];} enumerated;')
s=s.replace('static int mt6323_dapm_widgets[1],mtk_audio_map[1],mt6323_snd_controls[1],mt6323_UL_Codec_controls[1],mt6323_Voice_Switch[1],mt6323_pmic_Test_controls[1],mt6323_snd_Speaker_controls[1],', 'static int mt6323_dapm_widgets[1],mtk_audio_map[1],')
service='''
static DEFINE_MUTEX(Ana_Ctrl_Mutex);
static DEFINE_MUTEX(Ana_Power_Mutex);
#define ZCD_CON1 31
#define AUDTOP_CON7 37
#define SPK_CON9 39
static int Speaker_pga_gain,mAudio_Analog_Mic1_mode,mAudio_Analog_Mic2_mode,Codec_Loopback_Mode;

static int service_calls;
static void analog_sentinel(void){service_calls++;CHECK(false);}
static bool TurnOnADcPowerACC(int d,bool b){(void)d;(void)b;analog_sentinel();return false;}
static bool TurnOnADcPowerDCC(int d,bool b){(void)d;(void)b;analog_sentinel();return false;}
static bool TurnOnADcPowerDCCECM(int d,bool b){(void)d;(void)b;analog_sentinel();return false;}
static bool TurnOnADcPowerDmic(int d,bool b){(void)d;(void)b;analog_sentinel();return false;}
static bool AudioPreAmp1_Sel(int d){(void)d;analog_sentinel();return false;}
static bool AudioPreAmp2_Sel(int d){(void)d;analog_sentinel();return false;}
static int Apply_Ext_Amp_Gain(int d){(void)d;analog_sentinel();return -999;}
static void Headphone_Speaker_Switch_Change(bool b){(void)b;analog_sentinel();}
static void Headset_Speaker_Amp_Change(bool b){(void)b;analog_sentinel();}
static void ADC_LOOP_DAC_Func(int d){(void)d;analog_sentinel();}
struct snd_kcontrol_new {const char *name;int (*get)(struct snd_kcontrol *,struct snd_ctl_elem_value *);int (*put)(struct snd_kcontrol *,struct snd_ctl_elem_value *);};
#define SOC_ENUM_EXT(n,e,g,p) {n,g,p}
'''
# Array sizes come from exact production declaration text.
array_names=set(re.findall(r'ARRAY_SIZE\((\w+)\)', '\n'.join(fs[n]['text'] for n in names)))
for n in sorted(array_names):
    m=re.search(r'static const char \*\s*(?:const\s+)?'+n+r'\[\]\s*=\s*\{[\s\S]*?\};',production)
    assert m,n
    service+=m[0]+'\n'
# Probe needs control arrays defined, while tables need callback prototypes.
prototypes='\n'.join('static int '+n+'_state(struct snd_kcontrol *,struct snd_ctl_elem_value *);' for n in sorted(names))
insertion=service+'\n'+prototypes+'\n'+stubs+'\n#include "generated/actual-control-tables.inc"\n'
s=s.replace('static void mt6323_codec_init_reg',insertion+'static void mt6323_codec_init_reg')
s=s.replace('void *c,void *w,size_t n){(void)c;(void)w;(void)n;CHECK(!owns', 'void *c,const void *w,size_t n){(void)c;(void)w;(void)n;CHECK(!owns')
s=s.replace('#include "generated/actual-codec-bodies.inc"','#include "generated/actual-codec-bodies.inc"\n#include "generated/extra-control-bodies.inc"')
s=s.replace('#include "lifecycle.c"','#define main supplied_main\n#include "lifecycle.c"\n#undef main\n#include "controls.c"')
(ROOT/'tests/controls-contract.c').write_text(s)
dispatch='\n'.join('if(fn=='+n+'_state){seen++;CHECK(fn(NULL,&v)==-ENODEV);}' for n in sorted(names))
arrays=','.join('{'+n+',ARRAY_SIZE('+n+')}' for t,n in tables)
test='''
static void check_controls(void){
 struct {const struct snd_kcontrol_new *p;size_t n;} arrays[]={'''+arrays+'''};
 unsigned int i,j,k,seen=0;struct snd_ctl_elem_value v={0};
 for(i=0;i<ARRAY_SIZE(arrays);i++)for(j=0;j<arrays[i].n;j++)for(k=0;k<2;k++){
 int (*fn)(struct snd_kcontrol *,struct snd_ctl_elem_value *)= k?arrays[i].p[j].put:arrays[i].p[j].get;
 '''+dispatch+'''
 }
 CHECK(seen==46&&service_calls==0&&locks==0);
}
int main(void){
 reset();check_controls();
 /* Pointer exists but defaults/readiness have not been published. */
 mCodec_data=calloc(1,sizeof(*mCodec_data));CHECK(mCodec_data&&!mInitCodec);check_controls();free(mCodec_data);mCodec_data=NULL;
 CHECK(core_probe()==0);detach();check_controls();
 printf("PASS all 46 actual registered callback pointers reject absent, partial-init and removed state (138 calls); no analog sentinel entered\\n");return 0;
}
'''
(ROOT/'tests/controls.c').write_text(test)
(ROOT/'evidence/controls-extraction.json').write_text(json.dumps({'actual_callback_bodies':receipts,'already_bound_callbacks':sorted(names&existing.keys()),'actual_table_sha256':H((raw+'\n').encode()),'unrelated_callback_sentinels':sorted(unrelated),'assertion_scope':'138 readiness rejections through actual registered pointers; no analog behavior claim'},indent=2)+'\n')
print('Prepared all46 production control registrations and actual callback bodies')
