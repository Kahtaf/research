from pathlib import Path
import os,resource,subprocess,hashlib,re,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route');b=Path('/srv/android/lineage24');llvm=b/'prebuilts/clang/host/linux-x86/clang-r584948b/bin'
for name in ['libcameracustom.so','libcam.metadataprovider.so','libcam.halsensor.so']:
 p=r/'public'/('lib64_'+name)
 if not p.exists():p=Path('/srv/android/asus-hardware-completeness-audit/public-selected')/('lib64_'+name)
 data=p.read_bytes();print('ELF',p,'SHA256',hashlib.sha256(data).hexdigest())
 elf=subprocess.run(['readelf','--dyn-syms','-W',str(p)],capture_output=True,text=True,check=True).stdout
 print('\n'.join(l for l in elf.splitlines() if re.search('constructCust|Metadata|OV5670|HM2051|OV2680|SENSOR_DRVNAME',l)))
 strings=[m.group().decode() for m in re.finditer(rb'[\x20-\x7e]{5,}',data)]
 print('STRINGS',json.dumps([s for s in strings if re.search('constructCust|DEVICE_|metadata|Metadata|OV5670|HM2051|OV2680|ov5670|hm2051|ov2680',s)]))
for rel in ['drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define_default.h','drivers/misc/mediatek/cam_cal/inc/cam_cal_define.h','drivers/misc/mediatek/ion/mtk/ion_drv.h']:
 p=b/'kernel/asus/p00a-fd'/rel;print('SOURCE',p)
 if p.exists():print('SHA256',hashlib.sha256(p.read_bytes()).hexdigest());print(p.read_text())
# Toolchain identity and small compile artifact retrieval; no camera code runs.
print('CLANG',subprocess.run([str(llvm/'clang'),'--version'],capture_output=True,text=True).stdout)
