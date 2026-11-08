from pathlib import Path
import re,hashlib,os
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24'); k=a/'kernel/asus/p00a-fd'
checks=[
(a/'hardware/interfaces/audio','name:|compile_multilib|hw_get_module|audio_hw_device_open|AUDIO_DEVICE_API_VERSION|legacy|vintf_fragments'),
(a/'hardware/interfaces/sensors/1.0/default','name:|compile_multilib|hw_get_module|SENSORS_DEVICE_API|vintf_fragments|poll\\('),
(a/'hardware/interfaces/camera/provider/2.4/default','name:|compile_multilib|hw_get_module|CAMERA_MODULE_API|vintf_fragments|legacy/0'),
(a/'frameworks/av/services/camera/libcameraservice','HAL1|HAL 1|HAL_VERSION_1_0|deviceVersion <|CAMERA_DEVICE_API_VERSION_1'),
(k/'arch/arm64/boot/dts/mediatek','asus-p00a|goodix|bma253|bmm|ap321|ov5670|ov2680|audio|sound'),
(k/'drivers/input/touchscreen/goodix.c','compatible|request_firmware|irq|reset|suspend|resume|input->name|touchscreen_parse'),
(k/'drivers/misc/mediatek/accelerometer/bma253','/data/|/persist/|DEVICE_ATTR|input|compatible'),
(k/'sound/soc/mediatek/mt8163','compatible|snd_soc_card|mt-soc-codec|Audio_Amp|Speaker_Amp|Headphone|ADC|Audio_i2s|DL1|VUL')]
for root,pattern in checks:
 print('\nROOT',root,'PATTERN',pattern)
 fs=[root] if root.is_file() else list(root.rglob('*')) if root.exists() else []
 hits=0
 for f in fs:
  if not f.is_file() or f.suffix not in ['.h','.c','.cpp','.bp','.xml','.rc','.dts','.dtsi'] or f.stat().st_size>2*1024*1024: continue
  if 'boot/dts' in str(root) and f.name not in ['asus-p00a.dts','mt8163.dtsi']: continue
  lines=f.read_text(errors='replace').splitlines(); matches=[(i+1,x) for i,x in enumerate(lines) if re.search(pattern,x,re.I)]
  if matches:
   print('FILE',f,'SHA256',hashlib.sha256(f.read_bytes()).hexdigest())
   for n,x in matches[:50]:print(f'{n}: {x}')
   hits+=len(matches)
   if hits>550:print('LIMIT');break
