#!/usr/bin/env python3
"""Hash-check saved primary sources and emit review excerpts without network."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
receipts=json.loads((ROOT/'evidence/source-receipts.json').read_text())['files']
ranges={
'kernel/init/main.c':[(280,319)],
'kernel/arch/arm64/kernel/setup.c':[(241,260)],
'kernel/arch/arm64/mm/init.c':[(60,80)],
'kernel/drivers/of/fdt.c':[(903,925),(1090,1128)],
'kernel/security/selinux/hooks.c':[(100,130),(6545,6565)],
'aosp/system/core/init/selinux.cpp':[(99,121),(432,443)],
'aosp/system/core/init/Android.bp':[(118,150)],
'aosp/system/core/init/property_service.cpp':[(1345,1358),(1390,1410)],
'aosp/system/fs/fs_mgr/libfstab/boot_config.cpp':[(111,152),(172,207)],
'aosp/system/fs/fs_mgr/libfstab/fstab.cpp':[(464,492),(768,788),(812,862)],
'aosp/device/asus/p00a/BoardConfig.mk':[(50,65)],
'aosp/device/asus/p00a/rootdir/fstab.mt8163':[(1,30)],
'aosp/build/release/flag_values/trunk_staging/RELEASE_PLATFORM_SDK_VERSION.textproto':[(1,10)],
'aosp/build/release/flag_values/cp2a/RELEASE_PLATFORM_SDK_VERSION.textproto':[(1,10)],
}
lines=[]
for name,spans in ranges.items():
    data=(ROOT/'source'/name).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==receipts[name]['sha256']
    text=data.decode().splitlines();lines+=[name+' SHA256 '+digest,'remote source '+receipts[name]['remote_path']]
    for first,last in spans:
        lines.extend(f'{i}: {text[i-1]}' for i in range(first,min(last,len(text))+1))
        lines.append('')
(ROOT/'evidence/source-excerpts.txt').write_text('\n'.join(lines)+'\n')
print('Saved hash-pinned primary-source excerpts')
