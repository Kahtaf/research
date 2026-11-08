from pathlib import Path
import json,hashlib,base64,subprocess
B=Path('/srv/android/asus-linux49-pmic-stage-capture-20261108-a1ff82b1');K=B/'kernel';O=B/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['arch/arm64/lib/delay.c','arch/arm64/include/asm/timex.h','arch/arm64/include/asm/arch_timer.h','include/clocksource/arm_arch_timer.h','arch/arm64/include/asm/delay.h','include/linux/delay.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','include/linux/asus_retained_trace.h','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/misc/mediatek/power/mt8163/pmic_mt6323.c','arch/arm64/kernel/head.S','arch/arm64/kernel/asus_entry_text.S','arch/arm64/boot/dts/asus/asus-p00a.dts','kernel/workqueue.c','drivers/power/supply/power_supply_core.c','drivers/power/supply/power_supply_leds.c','drivers/power/supply/power_supply_sysfs.c','drivers/misc/mediatek/video/mt8163/dispsys/ddp_rdma.c']
files={n:(K/n).read_bytes() for n in names if (K/n).is_file()}
for n in ['arch/arm64/lib/.delay.o.cmd','arch/arm64/kernel/.asus_retained_trace.o.cmd','include/generated/compile.h','include/generated/utsrelease.h','.config']:
 files['out-provenance/'+n]=(O/n).read_bytes()
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={x[3]:(int(x[0],16),int(x[1],16)) for l in nm.splitlines() if len(x:=l.split())==4}
targets=['__delay','__const_udelay','__udelay','__ndelay','asus_p00a_pmic_adc','asus_p00a_battery_get_property','arch_counter_get_cntvct']
dis={n:subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+s),str(O/'vmlinux')],text=True) for n,(a,s) in sized.items() if n in targets}
print(json.dumps(dict(base=str(B),source_link=str((O/'source').resolve()),config_sha256=sha(O/'.config'),image_sha256=sha(O/'arch/arm64/boot/Image.gz-dtb'),files={n:dict(sha256=hashlib.sha256(v).hexdigest(),data=base64.b64encode(v).decode()) for n,v in files.items()},disassembly=dis,symbols={n:dict(address=hex(a),bytes=s) for n,(a,s) in sized.items() if n in targets},compiler=subprocess.check_output(['aarch64-linux-gnu-gcc','--version'],text=True))))
