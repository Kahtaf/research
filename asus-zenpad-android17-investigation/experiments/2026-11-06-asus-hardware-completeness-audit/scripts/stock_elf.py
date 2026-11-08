from pathlib import Path
import subprocess,json,re,hashlib,os,struct
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
root=Path('/srv/android/asus-hardware-completeness-audit/public-selected'); root.mkdir(parents=True,exist_ok=True)
names=['hw/audio.primary.mt8163.so','hw/camera.mt8163.so','hw/sensors.mt8163.so','libcustom_nvram.so','libnvram.so','libnvram_platform.so','libnvram_daemon_callback.so','libfile_op.so','libcam.halsensor.so','libcamdrv.so','libcamdrv_FrmB.so','libcameracustom.so','libaudiocustparam.so','libhwm.so','libhwsensorhub.so']
results=[]
for arch in ['lib','lib64']:
 for name in names:
  p='/vendor/'+arch+'/'+name
  data=subprocess.run(['debugfs','-R','cat '+p,img],capture_output=True).stdout
  if not data.startswith(b'\x7fELF'): continue
  assert len(data)<16*1024*1024
  target=root/(arch+'_'+name.replace('/','_'));target.write_bytes(data)
  elf=subprocess.run(['readelf','-dWs',str(target)],capture_output=True,text=True).stdout
  strings=[s.decode('ascii') for s in re.findall(rb'[\x20-\x7e]{5,}',data)]
  paths=sorted(set(s for s in strings if re.search(r'/data/|/dev/|/sys/|/proc/|NVRAM|AP_CFG|BMA|bma|bmm|ap321|ov[0-9]|gc[0-9]|sp[0-9]',s)))
  syms=[line for line in elf.splitlines() if (' UND ' in line and re.search(r'nvram|NVM|Nvram|Audio|Sensor|Camera|Graphic|String8|Parcel|Memory|Fence|BHw',line)) or 'g_akCFG' in line or 'g_i4CFG' in line]
  results.append(dict(path=p,size=len(data),sha256=hashlib.sha256(data).hexdigest(),elfclass=data[4],needed=re.findall(r'Shared library: \[(.*?)\]',elf),selected_strings=paths,selected_symbols=syms))
print(json.dumps(results,indent=2))
for p in ['/etc/audio_policy_configuration.xml','/vendor/etc/audio_device.xml','/usr/idc/goodix-touchscreen.idc','/usr/keylayout/mtk-kpd.kl','/vendor/etc/partition_permission.sh']:
 r=subprocess.run(['debugfs','-R','cat '+p,img],capture_output=True,text=True)
 print('\nCONFIG',p);print(r.stdout)
