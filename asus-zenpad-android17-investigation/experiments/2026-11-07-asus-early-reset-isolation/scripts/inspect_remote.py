from pathlib import Path
import subprocess, json, hashlib
R=Path('/srv/android/asus-early-reset-isolation-20261107'); R.mkdir(exist_ok=False)
(R/'evidence').mkdir(); (R/'source').mkdir()
B=Path('/srv/android/asus-early-retained-kernel-probe-20261107'); K=B/'kernel'; O=B/'out'
print('PREFIXES', '\n'.join(str(p) for p in Path('/srv/android').iterdir() if p.is_dir()))
for n in ['drivers/watchdog/mtk_wdt.c','drivers/watchdog/Makefile','drivers/misc/mediatek/wd_drv/Makefile','drivers/misc/mediatek/wd_drv/wd_common_drv.c','arch/arm64/kernel/asus_retained_trace.c']:
 p=K/n
 if p.exists():
  data=p.read_text(); (R/'evidence'/n.replace('/','__')).write_text(data)
  print('\nSOURCE', n, '\n', '\n'.join(f'{i}: {l}' for i,l in enumerate(data.splitlines(),1)))
print('SEARCH',subprocess.run(['rg','-n','mtk_wdt_restart|mtk_wdt_restart|wdt_arch_reset|wdt_restart|mtk_wdt_mode_config|wd_api_init|mtk_wdt_set_time_out_value','drivers/misc/mediatek','drivers/watchdog'],cwd=K,capture_output=True,text=True).stdout)
p=subprocess.run(['aarch64-linux-gnu-nm','-n',str(O/'vmlinux')],capture_output=True,text=True,check=True)
lines=[l for l in p.stdout.splitlines() if any(x in l.lower() for x in ['wdt','watchdog','wd_api','kicker','asus_retained'])]
(R/'evidence/symbols.txt').write_text('\n'.join(lines)+'\n');print('SYMBOLS','\n'.join(lines))
print('DT',subprocess.run(['rg','-n','watchdog|toprgu|mt6589-wdt|mt8163-wdt|10007000','arch/arm64/boot/dts'],cwd=K,capture_output=True,text=True).stdout)
