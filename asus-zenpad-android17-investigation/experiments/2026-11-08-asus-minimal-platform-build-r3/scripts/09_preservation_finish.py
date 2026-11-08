from pathlib import Path
import base64,gzip,hashlib,json,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');O=R/'out';E=R/'evidence';F=Path('/srv/android/asus-minimal-platform-build-r2-20261108');I=Path('/srv/android/asus-minimal-platform-build-20261108');P=Path('/srv/android/asus-minimal-platform-preparation-20261108')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=E/'linked-verification.json';r=json.loads(p.read_text());nm=subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True);syms={l.split()[2] for l in nm.splitlines() if len(l.split())==3}
names=['mtkfb_probe','mtkfb_init','musb_init_controller','usb_init','mmc_init','msdc_drv_probe','msdc_drv_init','snd_init','alsa_sound_init','inet_init','kbase_init','kbase_platform_device_probe','mtk_vcodec_probe','tpd_probe','goodix_ts_probe','wmt_dev_init','setMaxbrightness','backlight_list_head','virtual_sensor_cooler_backlight_init']
assert all(n not in syms for n in names);r['removed_symbols']={n:'absent from actual vmlinux' for n in names};r['entry_literal_copies']=dict(count=2,purpose=['pre-MMU assembly entry payload','C retained writer authentication constant'],runtime_console_requires_one_fresh_entry=True)
p.write_text(json.dumps(r,indent=2)+'\n')
assert sha(F/'out/.config')=='6f8abd4290b19aad386770200825d3065e74fd8fb311d4b1b20c7af2cc621dc6';assert sha(I/'out/.config')=='add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb'
prepared=json.loads((P/'evidence/preparation-receipt.json').read_text())
for n,h in prepared['uploaded'].items():assert sha(P/n)==h,n
assert json.loads((F/'evidence/kernel-status.json').read_text())['exit']==2 and json.loads((I/'evidence/kernel-status.json').read_text())['exit']==2
assert sha(O/'System.map')==json.loads((E/'System.map-receipt.json').read_text())['uncompressed_sha256']
assert gzip.decompress((R/'artifacts/System.map.gz').read_bytes())==(O/'System.map').read_bytes()
record=dict(previous_two_failures_preserved=True,preparation_uploaded_sources_unchanged=True,all_kernel_commands=3,helper_compiles_total=1,helper_compiles_r3=0,kernel_source_changes_from_r2=['config-hash entry tag metadata only'],DT_and_helper_and_ramdisk_equal=True,System_map_genuine=True,vmlinux_out_left_remote=True,physical_contact=False,ready_for_one_local_offline_package=True)
(E/'preservation-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
files={}
for n in ['linked-verification.json','preservation-receipt.json']:
 d=(E/n).read_bytes();files['evidence/'+n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,preservation=record)))
