#!/usr/bin/env python3
import hashlib,json,re,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p):return (root/p).read_text()
def data(p):return json.loads(read(p))
assert data('evidence/stable-optional-boost/results.json')[-1]['exit_code']==0
assert data('evidence/asus-pruned/results.json')[-1]['exit_code']==2
missing=sorted(set(re.findall(r"undefined reference to `([^']+)'",read('evidence/asus-pruned/build.log'))))
assert missing==['chargin_hw_init_done','chr_control_interface'],missing
assert data('evidence/live-dt-index.json')['properties']==2075
assert data('evidence/board-wiring-verification.json')['checks']==13
objects=read('evidence/asus-linked-objects.txt')
for name in ['z380m_kd_rm68200g01_lcm_drv','goodix_ts_probe','AArch64','REL (Relocatable file)']:assert name in objects,name
config=read('build/asus-candidate/.config')
assert 'CONFIG_CUSTOM_KERNEL_LCM="z380m_kd_rm68200g01"' in config
assert 'CONFIG_TOUCHSCREEN_GOODIX=y' in config
for name in ['MTK_BQ24296_SUPPORT','MTK_BQ25601_SUPPORT','MMC_AMAZON_BOOT0_PL_BACKUP','USB_AMAZON_DOCK','SND_SOC_RT551X_SPI']:
 assert '# CONFIG_'+name+' is not set' in config,name
manifest=data('evidence/patch-manifest.json');assert len(manifest['files'])==18
for row in manifest['files']:
 for folder in ['sources/kernel','evidence/patch-replay']:
  assert hashlib.sha256((root/folder/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
dtb=root/'artifacts/asus-p00a-COMPILE-ONLY.dtb';assert struct.unpack('>I',dtb.read_bytes()[:4])[0]==0xd00dfeed
assert dtb.stat().st_size==61942
assert not (root/'build/asus-candidate/arch/arm64/boot/Image.gz-dtb').exists()
state=read('evidence/final-device-state.txt')
for x in ['uid=2000(shell)','P00A_2','NRD90M.WW_P00A-V5.3.20-20180809','green','com.google.android.gms','com.android.vending']:assert x in state,x
files=[root/'STATUS.md',root/'README.md',root/'DRIVER-MATRIX.md',*sorted((root/'patches').glob('*.patch')),dtb]
summary=dict(status='passed',meaning='Offline experiment results verified; ASUS final link remains blocked and no ASUS boot image exists',control_kernel_link='passed',asus_final_link='failed',unresolved_symbols=missing,compiled_asus_driver_symbols=['z380m_kd_rm68200g01_lcm_drv','goodix_ts_probe'],live_dt_properties=2075,wiring_checks=13,patch_replay_files=18,artifacts=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
(root/'evidence/result-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Verified control link, expected ASUS link failure, compiled panel/touch symbols, live DT wiring, config exclusions, patch replay and unchanged stock identity.')
