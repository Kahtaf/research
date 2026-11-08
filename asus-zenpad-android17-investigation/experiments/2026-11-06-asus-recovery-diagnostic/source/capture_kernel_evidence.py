#!/usr/bin/env python3
"""Optional READ-ONLY SSH source capture. No VM writes or builds.

Not part of offline generation. Outputs must not already exist.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    'drivers/input/keyboard/mediatek/mt8163/hal_kpd.c',
    'drivers/input/keyboard/mediatek/kpd.c',
    'drivers/input/keyboard/mediatek/Kconfig',
    'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_sw.h',
    'drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/upmu_hw.h',
    'drivers/misc/mediatek/power/mt8163/pmic_mt6323.c',
    'drivers/watchdog/mtk_wdt.c',
    'drivers/misc/mediatek/usb20/mt8163/usb20.c',
    'arch/arm64/boot/dts/mediatek/mt8163.dtsi',
    'arch/arm64/boot/dts/mediatek/asus-p00a.dts',
    'arch/arm64/kernel/process.c',
    'drivers/firmware/psci.c',
]

def main():
    remote='''import pathlib,hashlib,json,subprocess
root=pathlib.Path('/srv/android/asus-android17/kernel-bpf-fd')
files=FILES
result={'revision':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'files':{}}
for name in files:
 b=(root/name).read_bytes()
 assert len(b)<1000000
 result['files'][name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
print(json.dumps(result))
'''.replace('FILES',repr(FILES))
    home=Path.home()
    cmd=['ssh','-i',str(home/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes',
         '-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
         '-o','HostKeyAlias=compute.8549823276971553556',
         '-o',f'UserKnownHostsFile={home}/.ssh/google_compute_known_hosts',
         'android@IP_REDACTED','python3 -c '+shlex.quote(remote)]
    result=json.loads(subprocess.check_output(cmd,timeout=45))
    assert result['revision']=='717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
    local=ROOT.parent/'2026-11-05-asus-p00a-power-port/sources/kernel'
    out=ROOT/'source/kernel-reference';out.mkdir(exist_ok=False)
    for name,value in result['files'].items():
        data=(local/name).read_bytes()
        value['local_match']=hashlib.sha256(data).hexdigest()==value['sha256']
        assert value['local_match'],name
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
    with (ROOT/'evidence/kernel-source-identity.json').open('x') as f:
        f.write(json.dumps(result,indent=2)+'\n')
    print('Read-only source identities matched:',len(result['files']))

if __name__=='__main__':main()
