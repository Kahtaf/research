from pathlib import Path
import base64,hashlib,json,subprocess,re
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
primary=['drivers/soc/mediatek/mtk-pmic-wrap.c','drivers/base/regmap/regmap.c','drivers/mfd/mt6397-core.c','drivers/power/supply/mediatek/battery/battery_common.c','kernel/time/sched_clock.c']
preserved=['drivers/power/supply/power_supply_core.c','drivers/power/supply/power_supply_sysfs.c','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/misc/mediatek/power/mt8163/pmic_mt6323.c','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc','arch/arm64/lib/delay.c']
files={n:base64.b64encode((K/n).read_bytes()).decode() for n in primary}
def rec(p,do_hash=True):
 st=p.stat();d=dict(bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
 if do_hash:d['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
meta={str(p.relative_to(B)):rec(p,p.name!='vmlinux') for p in [O/'vmlinux',O/'.config',O/'System.map']}
hashes={n:rec(K/n) for n in primary+preserved}
matches=[]
for p in sorted((K/'drivers/clocksource').glob('*.c'))+[K/'arch/arm64/kernel/time.c']:
 for no,line in enumerate(p.read_text().splitlines(),1):
  if 'sched_clock_register' in line: matches.append(f'{p.relative_to(K)}:{no}:{line}')
search='\n'.join(matches)+'\n'
assert len(search)<10000
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-n','-S',str(O/'vmlinux')],text=True)
syms='\n'.join(l for l in nm.splitlines() if re.search(r' (?:.*sched_clock.*|arch_counter.*|arch_timer.*|.*pwrap.*|mt6397_probe|asus_p00a_pmic.*|.*pmic.*(?:read|config|prepare).*|regmap_(?:read|write|lock_spinlock.*|unlock_spinlock.*)|__delay|__const_udelay|battery_get_property|__regmap_init)$',l))+'\n'
print(json.dumps(dict(files=files,hashes=hashes,metadata=meta,registration_search=dict(method="scoped drivers/clocksource/*.c and arch/arm64/kernel/time.c registration-line search; rg absent",stdout=search),symbols=syms)))
