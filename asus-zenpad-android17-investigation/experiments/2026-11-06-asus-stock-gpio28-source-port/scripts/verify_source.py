import difflib,hashlib,json,re,resource,shutil
from pathlib import Path
from bounded import ROOT,run
from extract_tests import fn
H=lambda b:hashlib.sha256(b).hexdigest()
W=ROOT.parent;apiroot=W/'2026-11-05-asus-p00a-power-port/sources/kernel'
pins=json.loads((ROOT/'evidence/input-pins.json').read_text())
# Every original remains unchanged, including the parent-owned observation.
for p in pins:
 assert H((W/p['original']).read_bytes())==p['sha256']
 assert H((ROOT/p['copy']).read_bytes())==p['sha256']
rel=Path('sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c')
old=(ROOT/'preimage'/rel).read_text();new=(ROOT/'candidate'/rel).read_text()
unchanged=[]
for name in ['Speaker_Amp_Change','Speaker_Amp_Get','Speaker_Amp_Set','Apply_Speaker_Gain','Audio_Speaker_Class_Set','Audio_Speaker_Class_Get','Audio_Speaker_Pga_Gain_Set','Audio_Speaker_Pga_Gain_Get','Headset_Speaker_Amp_Change']:
 a=fn(old,name);b=fn(new,name);assert a==b,name;unchanged.append({'function':name,'sha256':H(a.encode())})
(ROOT/'evidence/internal-functions-unchanged.json').write_text(json.dumps(unchanged,indent=2)+'\n')
# Preprocess actual production translation units without substituting their logic.
# Only unavailable kernel #includes are removed. The new real header is inlined.
def strip(s):return '\n'.join(l for l in s.splitlines() if not l.startswith('#include '))+'\n'
helper=strip((ROOT/'candidate/sound/soc/mediatek/mt_soc_audio_8163/p00a_stock_gate.h').read_text())
full=new.replace('#include "p00a_stock_gate.h"',helper);full=strip(full)
source=ROOT/'tests/generated/codec-no-kernel-includes.c';source.write_text(full)
opts=['/usr/bin/clang','-E','-P','-x','c','-DCONFIG_OF=1','-DCONFIG_OF_GPIO=1','-DCONFIG_PINCTRL_MT8163=1','-DCONFIG_MTK_SPEAKER=1','-DCONFIG_GPIOLIB=1','-DCONFIG_ASUS_P00A_STOCK_SPEAKER_GATE=1']
pp=run(opts+[source],'evidence/candidate-codec-preprocessed.c').decode()
for name in ['AW8737_MODE4','switch_mode_delay','setUsingExtSpeaker','Audio_Ext_Speaker','mt_soc_get_dts_config','AudDrv_GPIO_EXTAMP_Select']:
 assert name not in pp,name
assert 'p00a_gate_set(enable)' in pp
assert pp.count('static int Ext_Speaker_Amp_Change(')==1
# All class-specific paths remain after actual preprocessor selection.
assert 'Speaker_ClassAB_Open();' in pp and 'Speaker_ClassAB_close();' in pp
# Profile guard is a real compile-time gate for contradictory configs.
guard=ROOT/'tests/generated/profile-guard.c';guard.write_text(helper)
for label,add,remove in [('aw-conflict',['-DCONFIG_AMP_AW8737S=1'],[]),('legacy-conflict',['-DCONFIG_MTK_LEGACY=1'],[]),('no-internal',[],['-DCONFIG_MTK_SPEAKER=1']),('no-of',[],['-DCONFIG_OF=1'])]:
 args=[a for a in opts if a not in remove]+add+[guard]
 out=run(args,'evidence/guard-'+label+'.txt',expect=1).decode();assert 'P00A stock gate requires OF/internal speaker' in out
# Verify precisely the two configuration-symbol deltas, without claiming olddefconfig.
def cfg(s):
 out={}
 for line in s.splitlines():
  m=re.match(r'(CONFIG_\w+)=(.*)',line)
  if m:out[m[1]]=m[2]
  m=re.match(r'# (CONFIG_\w+) is not set',line)
  if m:out[m[1]]='n'
 return out
configs=[]
for rel in ['resolved.config','arch/arm64/configs/asus_p00a_defconfig']:
 a=cfg((ROOT/'preimage'/rel).read_text());b=cfg((ROOT/'candidate'/rel).read_text());delta={k:{'before':a.get(k),'after':b.get(k)} for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
 assert delta=={'CONFIG_AMP_AW8737S':{'before':'y','after':'n'},'CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE':{'before':None,'after':'y'}},delta
 assert b['CONFIG_MTK_SPEAKER']=='y' and b['CONFIG_SND_SOC_MT8163']=='y'
 if rel=='resolved.config':assert all(b[k]=='y' for k in ['CONFIG_OF','CONFIG_OF_GPIO','CONFIG_PINCTRL_MT8163','CONFIG_GPIOLIB','CONFIG_SOUND','CONFIG_SND','CONFIG_SND_SOC'])
 configs.append({'path':rel,'pre_sha256':H((ROOT/'preimage'/rel).read_bytes()),'post_sha256':H((ROOT/'candidate'/rel).read_bytes()),'delta':delta,'all_other_symbols_identical':True,'olddefconfig_run':False})
k=(ROOT/'candidate/sound/soc/mediatek/Kconfig').read_text();entry=k[k.index('config ASUS_P00A_STOCK_SPEAKER_GATE'):]
assert 'default n' in entry and 'depends on SND_SOC_MT8163 && MTK_SPEAKER && OF && GPIOLIB' in entry and 'depends on !AMP_AW8737S && !MTK_LEGACY' in entry
(ROOT/'evidence/config-deltas.json').write_text(json.dumps(configs,indent=2)+'\n')
# Actual DTS preprocessor include closure, copied and pinned locally.
def copy_closure(path):
 target=ROOT/'inputs/dt-source'/path.relative_to(apiroot)
 if target.exists():return
 data=path.read_bytes();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 pins.append({'original':str(path.relative_to(W)),'copy':str(target.relative_to(ROOT)),'sha256':H(data),'bytes':len(data),'expected':None})
 text=data.decode()
 for item in re.findall(r'#include\s*[<"]([^>"]+)[>"]|/include/\s*"([^"]+)"',text):
  name=next(x for x in item if x);options=[path.parent/name,apiroot/'include'/name]
  found=next((p for p in options if p.is_file()),None);assert found,name;copy_closure(found)
copy_closure(apiroot/'arch/arm64/boot/dts/mediatek/mt8163.dtsi')
copy_closure(apiroot/'arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi')
copy_closure(apiroot/'include/dt-bindings/soc/mt8163-md32.h')
for version in ['preimage','candidate']:
 run(['/usr/bin/clang','-E','-P','-x','assembler-with-cpp','-nostdinc','-I',ROOT/'inputs/dt-source/arch/arm64/boot/dts/mediatek','-I',ROOT/'inputs/dt-source/include',ROOT/version/'arch/arm64/boot/dts/mediatek/asus-p00a.dts'],'evidence/'+version+'-dts-preprocessed.dts')
dts=(ROOT/'candidate/arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text();original=(ROOT/'preimage/arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text()
assert 'extspkamp-gpio = <&pio 28 0>;' in dts and 'asus,p00a-stock-speaker-gate;' in dts
assert all(x not in dts for x in ['aud_pins_extamp_high','aud_pins_extamp_low','extamp-pullhigh','extamp-pulllow','switch-mode-delay'])
# No edit of the USB controller or GPIO24 selector blocks.
for pattern in [r'&usb1 \{[^}]+\};',r'\tgpio24_sel: usb-dpn-sel-pin \{.*?\n\t\};']:
 a=re.search(pattern,original,re.S)[0];b=re.search(pattern,dts,re.S)[0];assert a==b
assert dts.count('MT8163_PIN_24_EINT2__FUNC_GPIO24')==1
# The original pinned compiled DT has exactly the codec node we merge, and pio controller.
import struct
def fdt(data):
 _,size,off,st,_,_,_,_,ss,sz=struct.unpack_from('>10I',data);strings=data[st:st+ss];end=off+sz;stack=[];nodes={}
 while off<end:
  tag=struct.unpack_from('>I',data,off)[0];off+=4
  if tag==1:
   n=data.index(0,off);stack.append(data[off:n].decode());off=(n+4)&~3;nodes['/'.join(stack) or '/']={}
  elif tag==2:stack.pop()
  elif tag==3:
   n,no=struct.unpack_from('>II',data,off);off+=8;name=strings[no:strings.index(0,no)].decode();nodes['/'.join(stack) or '/'][name]=data[off:off+n];off=(off+n+3)&~3
  elif tag==9:break
 return nodes
stock=fdt((ROOT/'inputs/research/inputs/stock-public/appended.dtb').read_bytes());base=fdt((ROOT/'inputs/research/inputs/bmc/asus-p00a.dtb').read_bytes())
assert stock['/soc/mt_soc_codec_name@11220000']['extspkamp-gpio']==struct.pack('>III',13,28,0)
assert base['/soc/mt_soc_codec_name@11220000']['compatible']==b'mediatek,mt8163-soc-codec-63xx\0'
# No GPIO28 pinmux assignment in pinned base DT; no assumed pull/drive state is added.
assign28=[n for n,p in base.items() if any(k in ['pins','pinmux'] and len(v)==4 and struct.unpack('>I',v)[0]>>8==28 for k,v in p.items())];assert not assign28
obs=json.loads((ROOT/'inputs/stock-gpio-ownership.json').read_text());assert obs['exit']==0 and not obs['gpio_or_pinctrl_write'];assert 'gpio-897 (spkamp-en-gpio' in obs['stdout'] and 'gpio-893 (USB_DPN_SEL' in obs['stdout']
(ROOT/'evidence/dt-and-ownership-checks.json').write_text(json.dumps({'pinned_stock_gpio_cells':[13,28,0],'candidate_binding':'/soc/mt_soc_codec_name@11220000/extspkamp-gpio = <&pio 28 0>','candidate_profile_boolean':True,'root_compatible':'asus,p00a','controller_compatible':'mediatek,mt8163-pinctrl','candidate_audio_gpio24_states_removed':True,'usb1_and_gpio24_selector_source_unchanged':True,'pinned_base_gpio28_pinmux_assignments':assign28,'dtc_or_target_dtb_build_run':False,'dts_validation':'actual C preprocessor include closure + pinned compiled-base node/ownership checks; full dtc validation deferred','parent_observation_utc':obs['utc'],'parent_observation_sha256':H((ROOT/'inputs/stock-gpio-ownership.json').read_bytes()),'global_numbers_in_candidate':False,'hardware_activity_by_agent':False},indent=2)+'\n')
# No hardcoded observed global numbering, guessed pulse delay or fitted amplifier name in helper.
for bad in ['869','897','893','AW8737_MODE','udelay(','msleep(']:assert bad not in helper
routes=W/'2026-11-06-asus-minimal-audio-hal/src/routes.c';data=routes.read_bytes();assert data.count(b'.qualified = false')==2
(ROOT/'evidence/HAL-unchanged.json').write_text(json.dumps({'path':str(routes.relative_to(W)),'sha256':H(data),'qualified_false_profiles':2,'mutated':False},indent=2)+'\n')
(ROOT/'evidence/input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print('PASS source/config/profile guards; internal bodies equal; DTS closure preprocessed; stock ownership pinned; HAL false')
