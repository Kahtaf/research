from pathlib import Path
import json,hashlib,re,gzip
R=Path(__file__).resolve().parents[1];S=R/'inputs'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fn(text,name):
 m=re.search(r'(?m)^(?:(?:static|inline|extern|int|void|bool|struct \w+|unsigned|__init|__must_check)\s+)+\**'+name+r'\s*\([^;]*?\)\s*\n\{',text)
 assert m,name
 start=m.start();p=m.end();depth=1
 while depth:depth+=(text[p]=='{')-(text[p]=='}');p+=1
 return text[start:p]+'\n'
checks={};records=[]
codec='sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c'
a=(S/'preimage'/codec).read_text();b=(S/'candidate'/codec).read_text()
for name in ['Speaker_Amp_Change','Speaker_Amp_Get','Speaker_Amp_Set','Apply_Speaker_Gain','Audio_Speaker_Class_Set','Audio_Speaker_Class_Get','Audio_Speaker_Pga_Gain_Set','Audio_Speaker_Pga_Gain_Get','Headset_Speaker_Amp_Change']:
 assert fn(a,name)==fn(b,name),name
 checks[name+'_unchanged']=True
parts=[]
for name in ['Ext_Speaker_Amp_Change','SavePowerState','RestorePowerState','SetAnalogSuspend','ADC_LOOP_DAC_Off','Ext_Speaker_Amp_Get','Ext_Speaker_Amp_Set','mt6323_codec_probe','mt6323_codec_remove','mtk_mt6323_codec_dev_probe','mtk_mt6323_codec_dev_remove','mtk_mt6323_codec_dev_shutdown','mtk_mt6323_codec_init']:parts.append(fn(b,name))
assert (S/'tests/generated/actual-codec-bodies.inc').read_text()=='\n'.join(parts)
helper=(S/'candidate/sound/soc/mediatek/mt_soc_audio_8163/p00a_stock_gate.h').read_text()
assert (S/'tests/generated/actual-gate.inc').read_text()=='\n'.join(l for l in helper.splitlines() if not l.startswith('#include '))+'\n'
checks['test_gate_codec_extraction_independently_verified']=True
parts=[]
for path,names in [('include/asm-generic/gpio.h',['gpio_is_valid','gpio_direction_output']),('drivers/gpio/gpiolib-legacy.c',['gpio_request_one']),('drivers/gpio/devres.c',['devm_gpio_release','devm_gpio_request_one']),('include/linux/device.h',['devm_add_action_or_reset']),('include/linux/of.h',['of_property_count_u32_elems']),('drivers/gpio/gpiolib-of.c',['of_get_named_gpio_flags'])]:
 for name in names:parts.append(fn((S/'inputs/api'/path).read_text(),name))
assert (S/'tests/generated/actual-api-bodies.inc').read_text()=='\n'.join(parts)
checks['test_gpio_api_extraction_independently_verified']=True
old=(S/'preimage/arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text();new=(S/'candidate/arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text()
for pattern in [r'&usb1 \{[^}]+\};',r'\tgpio24_sel: usb-dpn-sel-pin \{.*?\n\t\};']:
 assert re.search(pattern,old,re.S)[0]==re.search(pattern,new,re.S)[0]
checks['usb_controller_and_selector_source_unchanged']=True
for v in json.loads((S/'evidence/api-line-receipts.json').read_text()):
 p=S/v['copy'];assert h(p)==v['sha256'];assert v['match'] in p.read_text().splitlines()[v['line']-1]
checks['all_api_line_receipts_verified']=True
pins=json.loads((S/'evidence/input-pins.json').read_text())
for v in pins:
 p=R.parent/v['original'];assert h(p)==v['sha256'],str(p)
checks['all_allowlisted_original_inputs_unchanged']=True
routes=json.loads((S/'evidence/HAL-unchanged.json').read_text());p=R.parent/routes['path'];assert h(p)==routes['sha256'] and p.read_bytes().count(b'.qualified = false')==2
checks['HAL_both_profiles_false_and_hash_unchanged']=True
obs=R.parent/'2026-11-06-asus-stock-gpio-ownership/evidence/observation-1794011653421961000.json'
checks['parent_idle_receipt_sha256']=h(obs)
for v in json.loads((S/'evidence/pre-post-pins.json').read_text()):
 assert h(S/'candidate'/v['path'])==v['post_sha256']
checks['all_seven_candidate_postimages_exact']=True
(R/'evidence/static-verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
