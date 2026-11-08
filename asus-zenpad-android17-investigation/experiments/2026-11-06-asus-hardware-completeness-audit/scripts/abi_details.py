from pathlib import Path
import subprocess,re,json,struct
r=Path('/srv/android/asus-hardware-completeness-audit/public-selected');a=Path('/srv/android/lineage24')
obj=list((a/'prebuilts/clang/host/linux-x86').glob('clang-*/bin/llvm-objdump'))[-1]
for sym in ['NVM_GetCfgFileTable','NVM_GetFileDesc','NVM_GetLIDByName']:
 print('\nFUNCTION',sym);print(subprocess.run([str(obj),'--disassemble-symbols='+sym,str(r/'lib64_libnvram.so')],capture_output=True,text=True).stdout)
k=a/'kernel/asus/p00a-fd'
for sub in ['drivers/misc/mediatek/Makefile','drivers/misc/mediatek/accelerometer/Makefile','drivers/misc/mediatek/alsps/Makefile','drivers/misc/mediatek/magnetometer/Makefile','sound/soc/mediatek/Makefile']:
 p=k/sub;print('\nFILE',p);print(p.read_text() if p.exists() else 'ABSENT')
for sub in ['sound/soc/mediatek','drivers/misc/mediatek/accelerometer','drivers/misc/mediatek/alsps','drivers/misc/mediatek/magnetometer']:
 print('DIR',sub,[f.name for f in (k/sub).iterdir()])
for f in k.glob('sound/soc/mediatek/mt_soc_audio_8163/*.c'):
 text=f.read_text(errors='replace')
 if any(x in text for x in ['snd_soc_card','of_device_id','Speaker_Amp']):
  print('\nFILE',f)
  for i,l in enumerate(text.splitlines(),1):
   if re.search(r'compatible|snd_soc_card|Speaker_Amp|Headphone_Amp|Audio_Amp|AW873|aw873|\".*(Switch|Mux|Volume|PGA)\"',l): print(i,l)
# strictly public stock binaries/configs only
img='/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img'
for p in ['/vendor/bin/bmm050d','/vendor/bin/bmm056d','/vendor/bin/msensord','/vendor/data/misc/ProjectConfig_Z380M.mk','/vendor/data/misc/ProjectConfig.mk']:
 b=subprocess.run(['debugfs','-R','cat '+p,img],capture_output=True).stdout
 print('\nSTOCK',p,'SIZE',len(b))
 for s in re.findall(rb'[\x20-\x7e]{5,}',b):
  t=s.decode();
  if re.search(r'/data/|/persist/|CUSTOM_KERNEL_(ACC|MAG|ALS|IMG)|BMC156|AP3425|GT6108',t):print(t)
