from pathlib import Path
import hashlib,json,subprocess,base64,io,zipfile
R=Path('/srv/android/asus-early-reset-isolation-20261107');B=Path('/srv/android/asus-early-retained-kernel-probe-20261107');K=B/'kernel';O=B/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(O/'.config')=='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696'
assert sha(O/'arch/arm64/boot/Image.gz-dtb')=='d94b26f4e806a0c86b28e42c7a8e7590bfefa96b5c91a50f3a80a05445c867b2'
build=json.loads((B/'evidence/build-receipt.json').read_text())
assert sha(O/'vmlinux')==build['artifacts']['vmlinux']['sha256']
nm=subprocess.run(['aarch64-linux-gnu-nm','-n',str(O/'vmlinux')],capture_output=True,text=True,check=True).stdout
names={l.split()[-1] for l in nm.splitlines() if l.split()}
expected_present=['mtk_wdt_probe','mtk_wdt_stop','mtk_wdt_start','mtk_wdt_ping','mtk_wdt_driver_init']
expected_absent=['mtk_wdt_restart','wd_api_init','wk_start_kick_cpu','wk_work_callback','wk_kthread','wdt_arch_reset','get_wd_api']
assert all(n in names for n in expected_present);assert all(n not in names for n in expected_absent)
paths=['drivers/watchdog/mtk_wdt.c','drivers/watchdog/Makefile','drivers/watchdog/mediatek/Makefile','drivers/watchdog/mediatek/wdk/Makefile','drivers/watchdog/mediatek/wdk/wd_common_drv.c','drivers/watchdog/mediatek/wdk/wd_api.c','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/boot/dts/mediatek/mt8163.dtsi']
receipt=dict(status='SOURCE_AND_EXACT_ELF_CHECKED_NO_DEFENSIBLE_RESET_FIX',vm_prefix=str(R),candidate_image_sha256='2a0d400811292ece957bb00f632f56aef8e5967643bd5a0184c10eaeea051533',image_gz_dtb_sha256=sha(O/'arch/arm64/boot/Image.gz-dtb'),config_sha256=sha(O/'.config'),vmlinux_sha256=sha(O/'vmlinux'),vmlinux_matches_original_build_receipt=True,source_pins={n:sha(K/n) for n in paths},present_symbols=expected_present,absent_symbols=expected_absent,source_modified=False,source_copy_needed=False,kernel_builds=0,new_candidates=0,installer_executions=0,device_contacted=False,no_full_tree_hash=True)
(R/'evidence/identity.json').write_text(json.dumps(receipt,indent=2)+'\n')
blob=io.BytesIO()
with zipfile.ZipFile(blob,'w',zipfile.ZIP_DEFLATED) as z:
 for p in (R/'evidence').iterdir():
  if p.is_file():z.write(p,'evidence/vm/'+p.name)
 z.write(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb','evidence/vm/asus-p00a.dtb')
print(base64.b64encode(blob.getvalue()).decode())
