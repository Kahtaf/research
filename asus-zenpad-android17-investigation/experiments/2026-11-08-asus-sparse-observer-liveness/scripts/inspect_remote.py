from pathlib import Path
import base64,hashlib,json,subprocess
B=Path('/srv/android/asus-arm64-delay-loop-observation-20261108-f3da846c')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['kernel/printk/printk.c','init/main.c','include/linux/asus_retained_trace.h',
       'arch/arm64/lib/delay.c','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h']
files={n:(B/'kernel'/n).read_bytes() for n in names}
print(json.dumps(dict(base=str(B),source_link=str((B/'out/source').resolve()),
    config_sha256=sha(B/'out/.config'),image_sha256=sha(B/'out/arch/arm64/boot/Image.gz-dtb'),
    release=(B/'out/include/generated/utsrelease.h').read_text(),
    compiler=subprocess.check_output(['aarch64-linux-gnu-gcc','--version'],text=True),
    files={n:dict(sha256=hashlib.sha256(v).hexdigest(),data=base64.b64encode(v).decode()) for n,v in files.items()})))
