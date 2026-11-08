from pathlib import Path
import subprocess,re,json,hashlib
R=Path('/srv/android/asus-early-reset-isolation-20261107'); B=Path('/srv/android/asus-early-retained-kernel-probe-20261107'); K=B/'kernel'; O=B/'out'
files=['drivers/watchdog/mediatek/Makefile','drivers/watchdog/mediatek/wdk/Makefile','drivers/watchdog/mediatek/wdk/wd_common_drv.c','drivers/watchdog/mediatek/wdk/wd_api.c','arch/arm64/boot/dts/mediatek/mt8163.dtsi','arch/arm64/kernel/asus_retained_trace.c','drivers/watchdog/watchdog_dev.c','drivers/watchdog/Kconfig']
for n in files:
 p=K/n
 if not p.exists():continue
 text=p.read_text();(R/'evidence'/n.replace('/','__')).write_text(text)
 if n.endswith('mt8163.dtsi'):ranges=[(255,280)]
 elif n.endswith('watchdog_dev.c'):ranges=[(100,240),(870,940)]
 elif n.endswith('Kconfig'):ranges=[(1,140)]
 elif n.endswith('wd_common_drv.c') or n.endswith('wd_api.c'):ranges=[(1,160),(450,550),(750,900),(1100,1250)]
 else:ranges=[(1,1000)]
 lines=text.splitlines();print('SOURCE',n)
 for a,b in ranges:
  print('\n'.join(f'{i+1}: {lines[i]}' for i in range(a-1,min(b,len(lines)))))
print('CONFIG','\n'.join(l for l in (O/'.config').read_text().splitlines() if re.search('WATCHDOG|WD_KICKER|DOUGLAS|GIZA|FIQ|PSCI|RESET_CONTROLLER|DTB|DTS|ASUS',l)))
for name in ['mtk_wdt_probe','mtk_wdt_stop','mtk_wdt_start','asus_retained_trace_early_init']:
 p=subprocess.run(['aarch64-linux-gnu-objdump','-d','--disassemble='+name,str(O/'vmlinux')],capture_output=True,text=True,check=True)
 (R/'evidence'/('disassembly-'+name+'.txt')).write_text(p.stdout);print(p.stdout)
print('DTFILES','\n'.join(str(p) for p in (O/'arch/arm64/boot/dts').rglob('*.dtb')))
print('KICKER SOURCES','\n'.join(str(p.relative_to(K)) for p in K.rglob('*') if p.is_file() and ('wd_common' in p.name or p.name=='wd_api.c')))
