import json,re,shutil
from audit import ROOT,SOURCE,REL,H,functions,masked,snapshot
from bounded import run

replay=ROOT/'work/patch-replay'
if not replay.exists():
    shutil.copytree(SOURCE/'preimage',replay)
    run(['/usr/bin/patch','--batch','--fuzz=0','-d',replay,'-p1','-i',SOURCE/'patches/lifecycle-from-gpio28-candidate.patch'],'patch-replay.log')
for p in (SOURCE/'candidate').rglob('*'):
    if p.is_file():assert p.read_bytes()==(replay/p.relative_to(SOURCE/'candidate')).read_bytes()
assert {str(p.relative_to(replay)) for p in replay.rglob('*') if p.is_file()}=={str(p.relative_to(SOURCE/'candidate')) for p in (SOURCE/'candidate').rglob('*') if p.is_file()}
post=(SOURCE/'candidate'/REL/'mt_soc_codec_63xx.c').read_text()
strip=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith('#include '))+'\n'
for n in ('p00a_stock_gate.h','codec_state_controls.h'):post=post.replace('#include "'+n+'"',strip((SOURCE/'candidate'/REL/n).read_text()))
(ROOT/'work/selected-codec-preprocess.c').write_text(strip(post))
defines=['CONFIG_OF','CONFIG_OF_GPIO','CONFIG_GPIOLIB','CONFIG_PINCTRL_MT8163','CONFIG_MTK_SPEAKER','CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE']
pp=run(['/usr/bin/clang','-E','-P','-x','c']+['-D'+d+'=1' for d in defines]+[ROOT/'work/selected-codec-preprocess.c'],'selected-codec-preprocessed.c')
for bad in ('AW8737_MODE4','switch_mode_delay','setUsingExtSpeaker','AudDrv_GPIO_EXTAMP_Select'):assert bad not in pp,bad
assert 'Speaker_ClassAB_Open()' in pp and 'Speaker_ClassAB_close()' in pp
audit=json.loads((ROOT/'evidence/source-audit.json').read_text())
for r in audit['actual_private_control_registrations']:
    assert r['callback']+'_state(' in pp,r
hal=json.loads((SOURCE/'inputs/prior/evidence/HAL-unchanged.json').read_text())
p=ROOT.parent/hal['path'];assert H(p.read_bytes())==hal['sha256']
assert len(re.findall(r'\.qualified\s*=\s*false',p.read_text()))==2

# Exact lock/API bodies for the manual source review, no rewriting of locks.
receipts=[];snippets=[]
paths=[SOURCE/'candidate'/REL/n for n in ('mt_soc_codec_63xx.c','AudDrv_Gpio.c','p00a_stock_gate.h')]
paths += [SOURCE/'inputs/api'/n for n in ('sound/core/control.c','sound/soc/soc-core.c','drivers/gpio/gpiolib.c','drivers/gpio/devres.c','drivers/base/devres.c','drivers/pinctrl/core.c','drivers/pinctrl/pinmux.c','drivers/pinctrl/mediatek/pinctrl-mtk-common.c')]
selected={'snd_ctl_elem_read_user','snd_ctl_elem_write_user','snd_ctl_elem_read','snd_ctl_elem_write','snd_ctl_add','snd_soc_add_codec_controls','snd_soc_add_controls','snd_soc_add_component_controls','gpiod_request','__gpiod_request','gpiod_direction_output_raw','_gpiod_direction_output_raw','gpiod_free_commit','pinctrl_request_gpio','pinctrl_gpio_free','pinctrl_gpio_direction_output','pinctrl_gpio_direction','pinctrl_select_state','pinctrl_commit_state','devres_release_all','release_nodes','mtk_gpio_direction_output','mtk_pmx_gpio_set_direction','mtk_gpio_set'}
for p in paths:
    for n,f in functions(p.read_text()).items():
        if n in selected or (p in paths[:3] and re.search(r'\b(?:mutex_lock|mutex_unlock|spin_lock_irq)\s*\(',masked(f['body']))):
            receipts.append({'source':str(p.relative_to(ROOT.parent)),'function':n,'line':f['line'],'sha256':H(f['text'].encode())})
            snippets.append('/* '+str(p.relative_to(ROOT.parent))+':'+str(f['line'])+' */\n'+f['text'])
(ROOT/'evidence/lock-source-bodies.c').write_text('\n'.join(snippets))
(ROOT/'evidence/lock-source-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')

mtk=ROOT/'work/old/tests/mtk-boundary.c'
actual=functions((SOURCE/'inputs/api/drivers/pinctrl/mediatek/pinctrl-mtk-common.c').read_text())
test=functions(mtk.read_text())
mtkpins=[]
for n in ('mtk_get_port','mtk_pmx_gpio_set_direction','mtk_gpio_set','mtk_gpio_direction_output'):
    assert actual[n]['text']==test[n]['text'];mtkpins.append({'function':n,'sha256':H(actual[n]['text'].encode())})
run(['/usr/bin/clang','-std=gnu89','-O0','-g','-Wno-implicit-function-declaration','-fsanitize=undefined','-fno-sanitize-recover=all',mtk,'-o',ROOT/'work/mtk-boundary'],'mtk-boundary-compile.log')
text=run([ROOT/'work/mtk-boundary'],'mtk-boundary-run.log');assert '6 injected regmap failures' in text
(ROOT/'evidence/preservation.json').write_text(json.dumps({'patch_replay':'all candidate files match exactly; fuzz0; new control header absent before replay','selected_preprocessing':'ClassAB retained; AW and GPIO24 EXTAMP select excluded; all46 boundary symbols present','HAL':hal,'mtk_actual_body_pins':mtkpins,'originals_rehashed':len(snapshot())},indent=2)+'\n')
print('PASS exact replay, selected preprocessing, HAL preservation, lock bodies and MTK error-loss reproduction')
