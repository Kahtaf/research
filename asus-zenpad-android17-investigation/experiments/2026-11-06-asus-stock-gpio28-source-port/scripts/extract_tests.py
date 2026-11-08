import re,json,hashlib
from pathlib import Path
from bounded import ROOT
G=ROOT/'tests/generated';G.mkdir(exist_ok=True);records=[]
def fn(text,name):
 # Definitions may span lines; skip declarations. Match only the opening function brace.
 m=re.search(r'(?m)^(?:(?:static|inline|extern|int|void|bool|struct \w+|unsigned|__init|__must_check)\s+)+\**'+name+r'\s*\([^;]*?\)\s*\n\{',text)
 assert m,name
 start=m.start();p=m.end();depth=1
 while depth:
  depth+= (text[p]=='{')-(text[p]=='}');p+=1
 return text[start:p]+'\n'
def extract(path,name):
 p=ROOT/path;s=fn(p.read_text(),name);records.append({'source':path,'function':name,'sha256':hashlib.sha256(s.encode()).hexdigest()});return s
codec='candidate/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c'
api='inputs/api/'
# Compile actual kernel GPIO/devres/OF adapter bodies, not a rewritten port model.
pieces=[]
for path,names in [(api+'include/asm-generic/gpio.h',['gpio_is_valid','gpio_direction_output']), (api+'drivers/gpio/gpiolib-legacy.c',['gpio_request_one']), (api+'drivers/gpio/devres.c',['devm_gpio_release','devm_gpio_request_one']), (api+'include/linux/device.h',['devm_add_action_or_reset']), (api+'include/linux/of.h',['of_property_count_u32_elems']), (api+'drivers/gpio/gpiolib-of.c',['of_get_named_gpio_flags'])]:
 for name in names:pieces.append(extract(path,name))
(G/'actual-api-bodies.inc').write_text('\n'.join(pieces))
names=['SavePowerState','RestorePowerState','SetAnalogSuspend','ADC_LOOP_DAC_Off','Ext_Speaker_Amp_Get','Ext_Speaker_Amp_Set','mt6323_codec_probe','mt6323_codec_remove','mtk_mt6323_codec_dev_probe','mtk_mt6323_codec_dev_remove','mtk_mt6323_codec_dev_shutdown','mtk_mt6323_codec_init']
parts=[]
for name in names:parts.append(extract(codec,name))
# Selected wrapper is extracted from the actual profile branch (the first definition).
parts.insert(0,extract(codec,'Ext_Speaker_Amp_Change'))
(G/'actual-codec-bodies.inc').write_text('\n'.join(parts))
# Real macro values; fixture supplies type/layout and mock kernel-service boundaries only.
s=(ROOT/(api+'include/linux/gpio.h')).read_text();macros='\n'.join(l for l in s.splitlines() if l.startswith('#define GPIOF_'))
(G/'actual-gpio-flags.inc').write_text(macros+'\n')
# Exact API declarations checked against the mock definitions by the host compiler.
protos=[]
for path,name in [(api+'include/linux/gpio.h','devm_gpio_request_one'),(api+'include/linux/device.h','devm_add_action'),(api+'include/linux/of_gpio.h','of_get_named_gpio_flags'),(api+'include/linux/of.h','of_parse_phandle_with_args'),(api+'include/linux/of.h','of_device_is_compatible'),(api+'include/linux/of.h','of_machine_is_compatible')]:
 text=(ROOT/path).read_text();m=re.search(r'(?m)^(?:extern )?(?:int|bool|struct \w+ \*)\s+'+name+r'\([^;]+;',text);assert m,name
 protos.append(m[0]);records.append({'source':path,'prototype':name,'exact':m[0]})
(G/'actual-api-prototypes.inc').write_text('\n'.join(protos)+'\n')
# No kernel-header include substitution inside production bodies except unavailable header imports.
helper=ROOT/'candidate/sound/soc/mediatek/mt_soc_audio_8163/p00a_stock_gate.h'
s=helper.read_text();(G/'actual-gate.inc').write_text('\n'.join(l for l in s.splitlines() if not l.startswith('#include '))+'\n')
records.append({'source':str(helper.relative_to(ROOT)),'sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'transformation':'remove only two Linux include lines; actual checked API bodies/prototypes compiled in fixture'})
(G/'actual-gpio24-backend.inc').write_text(extract('candidate/sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.c','AudDrv_GPIO_EXTAMP_Set'))
(ROOT/'evidence/host-production-extraction.json').write_text(json.dumps(records,indent=2)+'\n')
print('Extracted',len(records),'production/API function or declaration receipts')

