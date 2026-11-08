#!/usr/bin/env python3
"""Fetch public source at a pinned commit; no remote files are created."""
import subprocess, pathlib, json, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
REV = '717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
SSH = ['ssh', '-i', str(pathlib.Path.home()/'.ssh/asus_p00a_android17'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556', '-o', 'UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'), 'android@IP_REDACTED']
paths = ['arch/arm64/boot/dts/mediatek/asus-p00a.dts', 'arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi', 'arch/arm64/configs/asus_p00a_defconfig', 'drivers/power/supply/mediatek/battery/Kconfig', 'drivers/power/supply/mediatek/battery/Makefile', 'drivers/power/supply/mediatek/battery/battery_common.c', 'drivers/power/supply/mediatek/battery/battery_meter.c', 'drivers/power/supply/mediatek/battery/switch_charging.c', 'drivers/misc/mediatek/power/mt8163/battery_meter_hal.c', 'drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.c', 'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/mtk_battery_meter.h', 'drivers/misc/mediatek/include/mt-plat/battery_meter_table.h', 'include/linux/power_supply.h']
import sys
paths = sys.argv[1:] or paths
manifest={}
for p in paths:
    assert '..' not in pathlib.PurePosixPath(p).parts and not p.startswith('/')
    assert all(c.isalnum() or c in '/_.-' for c in p)
    data=subprocess.check_output(SSH+['git -C /srv/android/asus-android17/kernel-bpf-fd show '+REV+':'+p])
    out=ROOT/'evidence/base'/p
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(data)
    manifest[p]=hashlib.sha256(data).hexdigest()
old=ROOT/'evidence/remote-source.json'
m=json.loads(old.read_text()) if old.exists() else {'revision':REV,'ssh':SSH,'operation':'git show (read only)','sha256':{}}
m['sha256'].update(manifest)
old.write_text(json.dumps(m,indent=2)+'\n')
print('Fetched',len(paths),'pinned source files; no remote writes/builds.')
