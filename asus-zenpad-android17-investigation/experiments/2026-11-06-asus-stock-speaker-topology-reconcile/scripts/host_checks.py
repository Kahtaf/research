"""Host-only execution of verbatim source fragments against event-recording boundaries."""
import json,re,hashlib
from pathlib import Path
from bounded import ROOT,run
G=ROOT/'evidence/host';G.mkdir(exist_ok=True)
rel='sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c'
combined=(ROOT/'inputs/combined'/rel).read_text();oem=(ROOT/'inputs/oem/asus-original/kernel-3.18'/rel).read_text()
def function(s,name):
 m=re.search(r'(?m)^static (?:int|void) +(?:__init )?'+name+r'\([^;]+?\n\{',s);assert m,name
 start=m.start();p=m.end();depth=1
 # These functions have no braces inside strings/comments affecting balance.
 while depth:
  if s[p]=='{':depth+=1
  if s[p]=='}':depth-=1
  p+=1
 return s[start:p]+'\n'
shim=r'''
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#define CONFIG_OF 1
#define pr_debug(...) ((void)0)
#define pr_err(...) ((void)0)
#define PRINTK_AUDDRV(...) ((void)0)
#define spin_lock_irq(x) ((void)(x))
#define spin_unlock_irq(x) ((void)(x))
#define __init
static int switch_mode_delay=0, switch_mode_lock;
static int gpio_count,select_count,delay_count,warm_count,register_count;
static char seq[128];static int nseq;
static int AudDrv_GPIO_EXTAMP_Select(int x){select_count++;seq[nseq++]=x?'H':'L';return 0;}
static void gpio_set_value(unsigned int pin,int x){gpio_count++;printf("gpio:%u=%d ",pin,x);seq[nseq++]=x?'H':'L';}
static void udelay(unsigned int x){delay_count++;printf("udelay:%u ",x);}
static void msleep(unsigned int x){warm_count++;printf("msleep:%u ",x);}
'''
receipts=[]
for label,src in [('oem',oem),('combined',combined)]:
 begin=src.index('#ifdef CONFIG_OF',src.index('static int Speaker_Amp_Set'))
 end=src.index('static int Ext_Speaker_Amp_Get',begin)
 frag=src[begin:end]
 (G/f'{label}-external-verbatim.inc').write_text(frag)
 for enabled in ([False] if label=='oem' else [True,False]):
  name=label+('-aw-on' if enabled else '-aw-off')
  defs='#define CONFIG_MTK_SPEAKER 1\n'+('#define CONFIG_AMP_AW8737S 1\n' if enabled else '')
  main='''
int main(void){
#ifdef TEST_OEM
 pin_extspkamp=28; /* DT-derived test input, never a hardware access. */
#endif
 Ext_Speaker_Amp_Change(true);Ext_Speaker_Amp_Change(false);seq[nseq]=0;
 printf("seq=%s gpio=%d select=%d delay=%d warm=%d\\n",seq,gpio_count,select_count,delay_count,warm_count);
 return 0;
}
'''
  path=G/f'{name}.c';path.write_text(defs+('#define TEST_OEM\n' if label=='oem' else '')+shim+frag+main)
  obj=G/name
  run(['/usr/bin/clang','-O0','-Wno-unused-variable','-Wno-unused-function',path,'-o',obj],output=f'evidence/host/{name}-compile.txt')
  out=run([obj],output=f'evidence/host/{name}-run.txt').decode()
  expected='seq=HL gpio=2 select=0 delay=0 warm=0' if label=='oem' else ('seq=HLHLHLHL gpio=0 select=8 delay=6 warm=1' if enabled else 'seq= gpio=0 select=0 delay=0 warm=0')
  assert expected in out,(name,out)
  pre=run(['/usr/bin/clang','-E','-P',path],output=f'evidence/host/{name}.i').decode()
  internal=G/f'{name}-internal.c';internal.write_text(defs+function(src,'Speaker_Amp_Change'))
  pp=run(['/usr/bin/clang','-E','-P',internal],output=f'evidence/host/{name}-internal.i')
  assert b'Speaker_ClassAB_Open();' in pp and b'Speaker_ClassAB_close();' in pp and b'Apply_Speaker_Gain();' in pp
  receipts.append({'variant':name,'result':out.strip(),'fragment_sha256':hashlib.sha256(frag.encode()).hexdigest(),'internal_preprocessed_sha256':hashlib.sha256(pp.strip()).hexdigest(),'MTK_SPEAKER':True,'AMP_AW8737S':enabled,'MTK_LEGACY':False,'CONFIG_OF':True})
assert receipts[1]['internal_preprocessed_sha256']==receipts[2]['internal_preprocessed_sha256']
# Actual DT has a matching audiosys node, but no switch-mode-delay anywhere.
nodeproof=json.loads((ROOT/'evidence/bmc-dt.json').read_text());assert not nodeproof['switch_mode_delay_nodes']
initfrag=function(combined,'mt_soc_get_dts_config')+function(combined,'mtk_mt6323_codec_init')
(G/'combined-init-verbatim.inc').write_text(initfrag)
initshim=r'''
struct device_node {int unused;};static struct device_node node;
static int mt_soc_codec_63xx_of_ids[1],mtk_codec_6323_driver;
static struct device_node *of_find_matching_node(struct device_node *n,void *ids){return &node;}
static int of_property_read_u32(struct device_node *n,const char *p,int *v){return -EINVAL;}
static int platform_driver_register(void *p){register_count++;return 0;}
'''
for enabled in [True,False]:
 name='init-aw-'+('on' if enabled else 'off');path=G/f'{name}.c';path.write_text(('#define CONFIG_AMP_AW8737S 1\n' if enabled else '')+shim+initshim+initfrag+'\nint main(void){int r=mtk_mt6323_codec_init();printf("ret=%d registration=%d\\n",r,register_count);return 0;}\n')
 run(['/usr/bin/clang','-O0','-Wno-unused-variable','-Wno-unused-function',path,'-o',G/name],output=f'evidence/host/{name}-compile.txt')
 out=run([G/name],output=f'evidence/host/{name}-run.txt').decode();assert out==('ret=-22 registration=0\n' if enabled else 'ret=0 registration=1\n')
 receipts.append({'variant':name,'result':out.strip(),'input':'matching DT node, missing required switch-mode-delay; mocks return real OF missing-property error','scope':'host source branch only, not kernel initialization'})
(ROOT/'evidence/host-checks.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(json.dumps(receipts,indent=2))
