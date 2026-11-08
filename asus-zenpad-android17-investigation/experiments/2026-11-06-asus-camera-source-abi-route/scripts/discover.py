from pathlib import Path
import subprocess, os, resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
def run(a):
 p=subprocess.run(a,text=True,capture_output=True,timeout=40);print('COMMAND',a,'RC',p.returncode);print(p.stdout[:22000]);print(p.stderr[:1000])
b=Path('/srv/android/lineage24')
for r in ['frameworks/av','frameworks/base','hardware/interfaces','hardware/libhardware','system/media']:
 run(['git','-C',str(b/r),'rev-parse','HEAD'])
for d in ['hardware/interfaces/camera/provider/2.4/default','hardware/interfaces/camera/device/1.0/default','frameworks/av/services/camera/libcameraservice/api1','frameworks/av/services/camera/libcameraservice/device1','frameworks/base/core/java/android/hardware/camera2/legacy','prebuilts/clang/host/linux-x86']:
 p=b/d; print('DIRECTORY',p); print('\n'.join(str(x) for x in p.iterdir()) if p.exists() else 'ABSENT')
run(['grep','-RnE','DeviceInfo1|DeviceInfo3|case 1:|HAL version|VERSION_1_0|mDeviceVersionMajor|major == 1|major != 3','/srv/android/lineage24/frameworks/av/services/camera/libcameraservice/common/hidl'])
run(['ls','/srv/android'])
