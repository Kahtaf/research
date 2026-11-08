from pathlib import Path
import json,hashlib,base64,os
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24');k=Path('/srv/android/asus-build-continuation/kernel'); files=[]
files+=list((k/'sound/soc/mediatek/mt_soc_audio_8163').glob('*.[ch]'))
files += [k/'arch/arm64/boot/dts/mediatek/asus-p00a.dts', k/'sound/soc/soc-core.c']
for pat in ['hardware/libhardware/include_all/hardware/audio*.h','external/tinyalsa/include/tinyalsa/*.h','external/tinyalsa/pcm.c','hardware/interfaces/audio/common/all-versions/default/service/*','hardware/interfaces/audio/core/all-versions/default/DevicesFactory.cpp','hardware/interfaces/audio/core/all-versions/default/Android.bp','hardware/interfaces/audio/effect/all-versions/default/Android.bp','hardware/interfaces/audio/core/all-versions/default/Stream.cpp','hardware/libhardware/modules/audio/audio_hw.c','system/sepolicy/vendor/hal_audio_default.te','system/sepolicy/public/hal_audio.te','system/sepolicy/private/hal_audio.te','hardware/interfaces/audio/7.1/config/*.xsd']:
 files+=list(a.glob(pat))
stock=Path('/srv/android/asus-hardware-completeness-audit/public-selected')
files += [p for p in stock.glob('*') if p.is_file() and p.stat().st_size<150000 and '.so' not in p.name]
result={}
for p in files:
 if p.is_file():result[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'data':base64.b64encode(p.read_bytes()).decode()}
print(json.dumps(result))
