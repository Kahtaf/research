from pathlib import Path
import subprocess,re
R=Path('/srv/android/asus-early-reset-isolation-20261107'); B=Path('/srv/android/asus-early-retained-kernel-probe-20261107'); K=B/'kernel'; O=B/'out'
print('PREFIXES', '\n'.join(str(p) for p in Path('/srv/android').iterdir() if p.is_dir()))
for p in (R/'evidence').iterdir():
 print('\nSOURCE',p.name,'\n','\n'.join(f'{i}: {l}' for i,l in enumerate(p.read_text().splitlines(),1)))
for directory,pattern in [('drivers/misc/mediatek',r'mtk_wdt_restart|wdt_arch_reset|wdt_restart|mtk_wdt_mode_config|mtk_wdt_set_time_out_value|__weak.*wd|wd_api_init'),('arch/arm64/boot/dts',r'watchdog|toprgu|mt6589-wdt|mt8163-wdt|10007000')]:
 for p in (K/directory).rglob('*'):
  if p.suffix not in ('.c','.h','.dts','.dtsi'):continue
  for i,l in enumerate(p.read_text(errors='replace').splitlines(),1):
   if re.search(pattern,l):print(f'{p.relative_to(K)}:{i}:{l}')
p=subprocess.run(['aarch64-linux-gnu-nm','-n',str(O/'vmlinux')],capture_output=True,text=True,check=True)
lines=[l for l in p.stdout.splitlines() if any(x in l.lower() for x in ['wdt','watchdog','wd_api','kicker','asus_retained'])]
(R/'evidence/symbols.txt').write_text('\n'.join(lines)+'\n');print('SYMBOLS','\n'.join(lines))
