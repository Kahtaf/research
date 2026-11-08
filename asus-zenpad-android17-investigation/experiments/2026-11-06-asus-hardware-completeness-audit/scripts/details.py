from pathlib import Path
import subprocess,hashlib
A=Path('/srv/android/lineage24');K=A/'kernel/asus/p00a-fd'
files={
'hardware/interfaces/audio/common/all-versions/default/service/Android.bp':None,
'hardware/interfaces/audio/common/all-versions/default/service/service.cpp':None,
'hardware/interfaces/audio/core/all-versions/default/DevicesFactory.cpp':(100,150),
'hardware/interfaces/sensors/1.0/default/Android.bp':None,
'hardware/interfaces/sensors/1.0/default/Sensors.cpp':(45,115),
'frameworks/av/services/camera/libcameraservice/CameraService.cpp':(1560,1595),
'frameworks/av/services/camera/libcameraservice/common/hidl/HidlProviderInfo.cpp':(1,45),
'kernel/asus/p00a-fd/arch/arm64/boot/dts/mediatek/asus-p00a.dts':None,
'kernel/asus/p00a-fd/drivers/input/touchscreen/goodix.c':(580,850),
}
for s,r in files.items():
 f=A/s
 if not f.exists(): print('MISSING',f);continue
 print('\nFILE',f,'SHA256',hashlib.sha256(f.read_bytes()).hexdigest())
 lines=f.read_text().splitlines();lo,hi=r or (1,len(lines))
 for n in range(lo-1,min(hi,len(lines))): print(f'{n+1}: {lines[n]}')
for args in [
 ['grep','-RnE','bma253|BMA253|bmm|BMM|ap321|AP321',str(K/'arch/arm64/boot/dts/mediatek')],
 ['grep','-RnE','mt8163.*audio|sound|audgpio|mt-soc-codec|mt-soc-aud',str(K/'arch/arm64/boot/dts/mediatek/mt8163.dtsi')],
 ['grep','-RnE','/persist/|/data/|bma|bmm|ap321|gt6108','/srv/android/asus-hardware/sources/kernel/arch/arm64/boot/dts/mediatek/asus-p00a.dts'],
 ['grep','-RnE','HAL1|VERSION_1_0|not supported',str(A/'hardware/interfaces/camera/provider/2.4/default/LegacyCameraProviderImpl_2_4.cpp')],
 ['grep','-RnE','AUDIO_DEVICE_API_VERSION_MIN',str(A/'hardware/libhardware/include_all/hardware/audio.h')],
 ]:
 r=subprocess.run(args,capture_output=True,text=True);print('\nQUERY',args, '\n',r.stdout[:20000],r.stderr)
