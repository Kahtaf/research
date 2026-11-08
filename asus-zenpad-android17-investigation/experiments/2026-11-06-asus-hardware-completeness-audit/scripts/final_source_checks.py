from pathlib import Path
import subprocess,re,hashlib,json,os
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
a=Path('/srv/android/lineage24'); k=a/'kernel/asus/p00a-fd'
for root,pat in [
 (a/'system/sepolicy',r'/dev/(snd|input|video|gsensor|msensor|camera|m_acc|hwmsensor)|hal_sensors_default|hal_audio_default|sysfs_wakeup|suspend_control'),
 (a/'build/make/target/product',r'audio.primary|audio_policy_configuration|android.hardware.audio.service|android.hardware.sensors|android.hardware.camera.provider'),
 (a/'frameworks/native/services/sensorservice',r'getService|ISensors|1_0|V1_0'),
 (k/'drivers/misc/mediatek/imgsensor',r'compat_ioctl|CONFIG_COMPAT|KDIMGSENSORIOC|kd_camera_hw'),
 (k/'sound/soc/mediatek/mt_soc_audio_8163',r'CONFIG_AMP_AW8737S|Audio_Amp_R_Switch|Audio_Amp_L_Switch|Ext_Speaker_Amp_Switch|Audio_ADC_1_Switch|Audio_ADC_2_Switch'),
]:
 print('\nROOT',root,'PATTERN',pat);total=0
 for f in root.rglob('*'):
  if not f.is_file() or f.suffix not in ['.c','.cpp','.h','.te','.mk'] and f.name not in ['file_contexts','genfs_contexts']: continue
  lines=f.read_text(errors='replace').splitlines();hits=[(i+1,l) for i,l in enumerate(lines) if re.search(pat,l)]
  if hits:
   print('FILE',f)
   for i,l in hits[:30]:print(i,l)
   total+=len(hits)
   if total>140:print('LIMIT');break
for rel,lo,hi in [('drivers/input/touchscreen/goodix.c',525,580),('drivers/input/touchscreen/goodix.c',810,886),('arch/arm64/boot/dts/mediatek/mt8163.dtsi',1040,1105)]:
 p=k/rel;print('\nFILE',p)
 for i,l in enumerate(p.read_text().splitlines(),1):
  if lo<=i<=hi:print(i,l)
# Compiled physical handoff DT, decompile to stdout only.
p=Path('/srv/android/asus-build-continuation/integration-r5/asus-p00a.dtb')
r=subprocess.run(['dtc','-I','dtb','-O','dts',str(p)],capture_output=True,text=True)
print('COMPILED_DT_SHA',hashlib.sha256(p.read_bytes()).hexdigest(),'DTC_EXIT',r.returncode)
lines=r.stdout.splitlines()
for i,l in enumerate(lines):
 if re.search(r'bmc156|ap3425|goodix|audiosys|allow-battery-charging',l):print('\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-2),min(len(lines),i+8))))
# Public libnvram GOT relocations disambiguate NVM_GetCfgFileTable branch.
p=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_libnvram.so')
print('\nNVRAM RELOCATIONS')
r=subprocess.run(['readelf','-rW',str(p)],capture_output=True,text=True)
for l in r.stdout.splitlines():
 if 'g_i4CFG' in l or 'g_akCFG' in l:print(l)
