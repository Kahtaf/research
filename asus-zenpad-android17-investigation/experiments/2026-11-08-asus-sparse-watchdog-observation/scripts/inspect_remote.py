from pathlib import Path
import base64,hashlib,json,subprocess
B=Path('/srv/android/asus-sparse-observer-liveness-20261108-e6799dac');K=B/'kernel';O=B/'out'
names=['drivers/watchdog/mtk_wdt.c','drivers/watchdog/Makefile','drivers/watchdog/watchdog_core.c','kernel/reboot.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','drivers/misc/mediatek/Makefile','drivers/misc/mediatek/wdk/Makefile']
files={n:(K/n).read_bytes() for n in names if (K/n).is_file()}
config=(O/'.config').read_text()
syms=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
selected=[l for l in syms.splitlines() if any(x in l.split()[-1] for x in ['mtk_wdt','mtk_reset','watchdog_init','restart_handler','do_kernel_restart','__delay'])]
dis={}
for l in selected:
 x=l.split()
 if len(x)==4 and x[2].lower()=='t':
  a,z=int(x[0],16),int(x[1],16)
  dis[x[3]]=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(O/'vmlinux')],text=True)
print(json.dumps(dict(base=str(B),source_link=str((O/'source').resolve()),config_sha256=hashlib.sha256((O/'.config').read_bytes()).hexdigest(),image_sha256=hashlib.sha256((O/'arch/arm64/boot/Image.gz-dtb').read_bytes()).hexdigest(),config_selected=[l for l in config.splitlines() if any(x in l for x in ['WATCHDOG','WD_KICKER','DOUGLAS','GIZA','MT8163'])],symbols=selected,disasm=dis,files={n:dict(sha256=hashlib.sha256(v).hexdigest(),data=base64.b64encode(v).decode()) for n,v in files.items()})))
