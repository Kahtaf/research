from pathlib import Path
import json,hashlib,subprocess,base64
B=Path('/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4')
files=['drivers/misc/mediatek/video/mt8163/dispsys/'+n for n in ['ddp_drv.c','ddp_irq.c','ddp_reg.h']]+['arch/arm64/kernel/asus_entry_tag.h']
print(json.dumps(dict(files={n:dict(sha256=hashlib.sha256((B/'kernel'/n).read_bytes()).hexdigest(),data=base64.b64encode((B/'kernel'/n).read_bytes()).decode()) for n in files},config_OF='CONFIG_OF=y' in (B/'out/.config').read_text(),requests=subprocess.check_output(['grep','-RnE','request_irq|disp_register_dev_irq|disp_init_irq',str(B/'kernel/drivers/misc/mediatek/video/mt8163')],text=True))))
