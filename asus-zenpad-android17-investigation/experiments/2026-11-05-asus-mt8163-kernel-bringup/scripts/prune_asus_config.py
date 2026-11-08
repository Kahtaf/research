#!/usr/bin/env python3
import re
from pathlib import Path
from source_edits import SOURCE
p=SOURCE/'arch/arm64/configs/asus_p00a_defconfig';s=p.read_text()
for name in ['USB_AMAZON_DOCK','MMC_AMAZON_BOOT0_PL_BACKUP','SND_SOC_RT551X_SPI','SND_SOC_RT551X_TEST_ONLY','SND_SOC_RT551X']:
 s=re.sub(r'^(?:CONFIG_'+name+r'=.*|# CONFIG_'+name+r' is not set)\n','',s,flags=re.M)
 s+='# CONFIG_'+name+' is not set\n'
p.write_text(s)
