from pathlib import Path
import subprocess,json,hashlib,re
R=Path('/srv/android/asus-early-reset-isolation-20261107');B=Path('/srv/android/asus-early-retained-kernel-probe-20261107');K=B/'kernel';O=B/'out'
p=subprocess.run([str(O/'scripts/dtc/dtc'),'-I','dtb','-O','dts',str(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb')],capture_output=True,text=True,check=True)
d=p.stdout
for name in ['toprgu@10007000','ram_console','chosen']:
 for m in re.finditer(r'[^\n]*'+re.escape(name)+r'[^\n]*\{',d):
  end=d.index('};',m.end())+2; print(d[m.start():end])
print('weak/header search')
for n in ['drivers/misc/mediatek/include/mt-plat/aee.h','drivers/misc/mediatek/include/mt-plat/mtk_wd_api.h','drivers/watchdog/mediatek/include/ext_wd_drv.h','drivers/watchdog/mediatek/wdt/mt_wdt.c','drivers/watchdog/mediatek/wdt/common/mtk_wdt.c']:
 p=K/n
 if not p.exists():continue
 data=p.read_text();(R/'evidence'/n.replace('/','__')).write_text(data)
 ls=data.splitlines()
 for i,l in enumerate(ls):
  if re.search('mtk_wdt_restart|__weak|weak\)|wdt_arch_reset',l): print(n,i+1,'\n'.join(ls[max(0,i-4):i+7]))
print('DT status overrides', '\n'.join(l for l in (K/'arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text().splitlines() if re.search('toprgu|wdt',l)))
print('BUILD OBJECT COMMAND',(O/'drivers/watchdog/.mtk_wdt.o.cmd').read_text()[:2500])
