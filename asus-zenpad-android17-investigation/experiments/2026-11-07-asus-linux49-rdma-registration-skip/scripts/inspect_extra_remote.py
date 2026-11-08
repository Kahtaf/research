from pathlib import Path
import json,base64
B=Path('/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4/kernel/drivers/misc/mediatek/video/mt8163')
files={str(p.relative_to(B)):base64.b64encode(p.read_bytes()).decode() for p in [B/'dispsys/ddp_hal.h',B/'dispsys/ddp_info.c']}
s=(B/'videox/primary_display.c').read_text().splitlines()
print(json.dumps(dict(files=files,primary_requests='\n'.join(s[3380:3440]+s[5310:5370]))))
