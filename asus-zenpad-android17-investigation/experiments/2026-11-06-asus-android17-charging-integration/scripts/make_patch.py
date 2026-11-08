#!/usr/bin/env python3
"""Create an incremental patch in an owned subset repository, never a live tree."""
from pathlib import Path
import subprocess,shutil,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'evidence/patch-work';S=R/'staged';B=R/'source/kernel-after-soc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True,stderr=subprocess.STDOUT)
if W.exists():shutil.rmtree(W)
shutil.copytree(B,W)
git('init','-q');git('add','.');git('-c','user.name=Offline charging staging','-c','user.email=ACCOUNT_REDACTED','commit','--no-gpg-sign','-qm','Frozen kernel after measurement and SOC')
shutil.copytree(S,W,dirs_exist_ok=True);git('add','-N','.');git('diff','--check')
name='0003-asus-p00a-checked-charging-integration.patch';data=git('diff','--binary','--full-index','--no-ext-diff')
(R/'patches'/name).write_text(data)
paths=[p.relative_to(S) for p in S.rglob('*') if p.is_file()]
manifest={'kernel_base':'717bb3c9e13ce573cfdd2dda856debd27a0fa17f','patch':name,'sha256':sha(R/'patches'/name),'prerequisites':{n:sha(R/'source'/n) for n in ['0001-asus-p00a-measured-battery.patch','0002-asus-p00a-checked-main-battery-soc.patch']},'files':{str(p):{'before':sha(B/p) if (B/p).exists() else None,'after':sha(S/p)} for p in paths}}
guards=['arch/arm64/boot/dts/mediatek/asus-p00a.dts','arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi','drivers/misc/mediatek/include/mt-plat/battery_meter_table.h','drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/mtk_battery_meter.h']
manifest['unchanged_guards']={p:sha(B/p) for p in guards}
(R/'evidence/patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(name,manifest['sha256'],len(paths),'files')
