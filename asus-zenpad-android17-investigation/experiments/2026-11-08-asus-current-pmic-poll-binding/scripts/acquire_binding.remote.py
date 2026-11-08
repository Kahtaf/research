from pathlib import Path
import base64,hashlib,json,subprocess,re
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
files={}
def add(n,p):
 d=p.read_bytes();assert len(d)<150000;files[n]=base64.b64encode(d).decode()
for n in ['drivers/clocksource/arm_arch_timer.c','arch/arm64/include/asm/arch_timer.h','arch/arm64/boot/dts/mediatek/mt8163.dtsi']:
 add(n,K/n)
for n in ['drivers/clocksource/Makefile','drivers/soc/mediatek/Makefile','drivers/soc/mediatek/Kconfig','drivers/misc/mediatek/power/mt8163/Makefile','drivers/misc/mediatek/power/mt8163/asus_p00a/Makefile']:
 add('evidence/build-metadata/'+n,K/n)
cmds={}
for n in ['drivers/soc/mediatek/mtk-pmic-wrap.o','drivers/base/regmap/regmap.o','drivers/mfd/mt6397-core.o','drivers/power/supply/mediatek/battery/battery_common.o','kernel/time/sched_clock.o','drivers/clocksource/arm_arch_timer.o','arch/arm64/lib/delay.o','drivers/misc/mediatek/power/mt8163/pmic_mt6323.o','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.o','drivers/power/supply/power_supply_core.o','drivers/power/supply/power_supply_sysfs.o','arch/arm64/boot/dts/mediatek/mt8163-evb.dtb']:
 p=O/n;q=p.parent/('.'+p.name+'.cmd')
 ent={'object_exists':p.exists(),'cmd_exists':q.exists()}
 if p.exists():
  st=p.stat();ent['object_metadata']=dict(bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
 if q.exists():
  d=q.read_bytes();st=q.stat();ent['cmd_metadata']=dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest(),mtime_ns=st.st_mtime_ns)
  # Preserve command and relevant dependency lines, not all generic headers.
  text=d.decode();ent['selected_lines']=[dict(line=i,text=l) for i,l in enumerate(text.splitlines(),1) if i==1 or any(x in l for x in ['arch_timer.h','timex.h','seqlock.h','pmic_battery.inc','asus_p00a_battery.h','mt8163.dtsi'])]
 cmds[n]=ent
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-n','-S',str(O/'vmlinux')],text=True)
want=['pwrap_read','pwrap_write','pwrap_regmap_read','pwrap_regmap_write','pwrap_probe','pwrap_node_to_regmap','regmap_lock_spinlock','regmap_unlock_spinlock','__regmap_init','regmap_read','regmap_write','_regmap_read','_regmap_write','mt6397_probe','battery_get_property','asus_p00a_battery_get_property','pmic_read_interface','pmic_config_interface','pmic_read_interface_nolock','pmic_config_interface_nolock','p00a_pmic_prepare_adc','asus_p00a_pmic_present','asus_p00a_pmic_adc','sched_clock','sched_clock_register','sched_clock_postinit','update_sched_clock','__delay','__const_udelay','arch_timer_common_init','arch_timer_of_init','arch_timer_detect_rate.part.0','arch_counter_get_cntvct','arch_counter_read','arch_timer_check_ool_workaround']
entries=[]
for l in nm.splitlines():
 a=l.split()
 if len(a)==4 and a[3] in want and a[2] in ['t','T']:
  # Exclude weak unrelated same-name legacy stub.
  address,size=int(a[0],16),int(a[1],16)
  assert size<20000
  out=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(address),'--stop-address='+hex(address+size),str(O/'vmlinux')])
  name='evidence/elf/'+a[3]+'.disasm';files[name]=base64.b64encode(out).decode();entries.append(dict(name=a[3],address=hex(address),size=size))
print(json.dumps(dict(files=files,cmd_receipts=cmds,disassembled=entries,missing_symbols=[n for n in want if n not in [e['name'] for e in entries]])))
