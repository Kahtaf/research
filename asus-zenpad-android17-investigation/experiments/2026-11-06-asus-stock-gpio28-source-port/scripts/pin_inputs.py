import gzip,hashlib,json,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT.parent
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
R=W/'2026-11-06-asus-stock-speaker-topology-reconcile';K=W/'2026-11-05-asus-p00a-power-port/sources/kernel'
manifest=json.loads(gzip.decompress((R/'inputs/context/2026-11-06-asus-bmc156-full-kernel/evidence/r5-source-manifest.json.gz').read_bytes()))
H=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def cp(p,out,expected=None):
 b=p.read_bytes();h=H(b)
 if expected:assert h==expected,(str(p),h,expected)
 d=ROOT/out;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
 rows.append({'original':str(p.relative_to(W)),'copy':out,'sha256':h,'bytes':len(b),'expected':expected})
 return b
rels=['sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c','sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.c','sound/soc/mediatek/Kconfig','arch/arm64/boot/dts/mediatek/asus-p00a.dts']
for rel in rels:
 b=cp(R/'inputs/combined'/rel,'preimage/'+rel,manifest[rel]);p=ROOT/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
for src,dest in [('inputs/bmc/asus_p00a_defconfig','arch/arm64/configs/asus_p00a_defconfig'),('inputs/bmc/resolved.config','resolved.config')]:
 b=cp(R/src,'preimage/'+dest);p=ROOT/'candidate'/dest;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
api=['include/linux/gpio.h','include/linux/gpio/consumer.h','include/linux/gpio/driver.h','include/asm-generic/gpio.h','include/linux/of.h','include/linux/of_gpio.h','include/linux/device.h','include/sound/soc.h','drivers/gpio/gpiolib.c','drivers/gpio/gpiolib-of.c','drivers/gpio/gpiolib-legacy.c','drivers/gpio/devres.c','drivers/base/devres.c','drivers/base/dd.c','drivers/pinctrl/core.c','drivers/pinctrl/pinmux.c','drivers/pinctrl/mediatek/pinctrl-mtk-common.c','drivers/pinctrl/mediatek/pinctrl-mtk-mt8163.h','sound/soc/soc-core.c','arch/arm64/boot/dts/mediatek/mt8163.dtsi','arch/arm64/boot/dts/mediatek/mt8163-pinfunc.h']
for rel in api:cp(K/rel,'inputs/api/'+rel,manifest[rel])
for src in ['inputs/stock-public/appended.dtb','inputs/bmc/asus-p00a.dtb','inputs/stock/audio_device.xml','inputs/stock/AudioParamOptions.xml','inputs/oem/asus-original/kernel-3.18/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c','evidence/stock-public-selected-symbols.json','evidence/stock-public-disassembly.txt','evidence/stock-public-codec-probe-disassembly.txt','evidence/gpio-ownership.json','evidence/stock-boot-match.json','evidence/address-mapping-controls.json','evidence/input-pins.json','report/HANDOFF.md']:
 cp(R/src,'inputs/research/'+src)
cp(W/'2026-11-06-asus-stock-gpio-ownership/evidence/observation-1794011653421961000.json','inputs/stock-gpio-ownership.json')
cp(W/'2026-11-06-asus-bmc156-full-kernel/report/SOURCE-PINS.json','inputs/BMC-SOURCE-PINS.json')
(ROOT/'evidence/input-pins.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'public inputs pinned')
