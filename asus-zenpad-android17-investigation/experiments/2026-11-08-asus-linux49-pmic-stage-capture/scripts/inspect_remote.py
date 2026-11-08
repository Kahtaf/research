from pathlib import Path
import json,hashlib,base64,subprocess
B=Path('/srv/android/asus-linux49-power-supply-phase-capture-20261107-431dfb9c');K=B/'kernel';O=B/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p='drivers/misc/mediatek/power/mt8163/'
names=[p+'asus_p00a/pmic_battery.inc',p+'asus_p00a/battery_diag.c',p+'pmic_mt6323.c',p+'Makefile',p+'asus_p00a/Makefile','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','include/linux/asus_retained_trace.h','include/linux/power/asus_p00a_battery.h','drivers/power/supply/power_supply_core.c','drivers/misc/mediatek/power/mt8163/battery_common.c','kernel/workqueue.c','include/linux/power_supply.h']
cmds=[p+'.pmic_mt6323.o.cmd',p+'asus_p00a/.battery_diag.o.cmd',p+'.built-in.o.cmd',p+'asus_p00a/.built-in.o.cmd','.vmlinux.cmd']
files={n:(K/n).read_bytes() for n in names if (K/n).is_file()}
for n in cmds:
 if (O/n).is_file():files['out-provenance/'+n]=(O/n).read_bytes()
q=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={x[3]:(int(x[0],16),int(x[1],16)) for l in q.splitlines() if len(x:=l.split())==4}
targets=['asus_p00a_pmic_present','asus_p00a_pmic_adc','p00a_pmic_prepare_adc','asus_p00a_battery_get_property','p00a_measurement_get_property','battery_get_property','pmic_read_interface','pmic_read_interface_nolock','pmic_config_interface','pmic_config_interface_nolock']
dis={n:subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+s),str(O/'vmlinux')],text=True) for n,(a,s) in sized.items() if n.split('.')[0] in targets}
print(json.dumps(dict(base=str(B),source_link=str((O/'source').resolve()),config_sha256=sha(O/'.config'),image_sha256=sha(O/'arch/arm64/boot/Image.gz-dtb'),map_sha256=sha(O/'System.map'),files={n:dict(sha256=hashlib.sha256(d).hexdigest(),data=base64.b64encode(d).decode()) for n,d in files.items()},disassembly=dis,symbols={n:dict(address=hex(a),bytes=s) for n,(a,s) in sized.items() if n.split('.')[0] in targets},config_lines=[l for l in (O/'.config').read_text().splitlines() if 'ASUS_P00A' in l or l.startswith('CONFIG_PREEMPT') or l.startswith('CONFIG_SMP') or l.startswith('CONFIG_NR_CPUS')])) )
