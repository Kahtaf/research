#!/usr/bin/env python3
import pathlib,json,hashlib,shutil,difflib
R=pathlib.Path('/srv/android/asus-build-continuation');D=R/'product-device';P=D/'radio/sepolicy/p00a_radio.te';F=D/'radio/sepolicy/file_contexts'
old=P.read_text();assert old.count('vendor_firmware_file')==4
new=old.replace('vendor_firmware_file','p00a_radio_firmware_file')
new=new.replace('type p00a_radio_device, dev_type;','type p00a_radio_device, dev_type;\ntype p00a_radio_firmware_file, vendor_file_type, file_type;')
P.write_text(new);f=F.read_text();newf=f+'/(vendor|system/vendor)/firmware/(WMT_SOC\\.cfg|WIFI_RAM_CODE_8163|ROMv2_lm_patch_1_[01]_hdr\\.bin) u:object_r:p00a_radio_firmware_file:s0\n';F.write_text(newf)
patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/radio/sepolicy/p00a_radio.te',tofile='b/radio/sepolicy/p00a_radio.te'))+''.join(difflib.unified_diff(f.splitlines(True),newf.splitlines(True),fromfile='a/radio/sepolicy/file_contexts',tofile='b/radio/sepolicy/file_contexts'))
(R/'evidence/radio-policy-compiler-fix.patch').write_text(patch)
receipt=R/'evidence/product-staging.json';shutil.copy2(receipt,R/'evidence/product-staging-r1.json');data=json.loads(receipt.read_text())
for p in [P,F]:data['changes'][str(p.relative_to(D))]['after']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
data['policy_fix']='SDK37 has no vendor_firmware_file type. Define dedicated vendor file type for the four exact radio firmware filenames.'
receipt.write_text(json.dumps(data,indent=2)+'\n')
