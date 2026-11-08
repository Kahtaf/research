#!/usr/bin/env python3
"""Prepare an isolated next product candidate; never modify active AOSP."""
import pathlib,shutil,hashlib,json,subprocess
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');active=A/'device/asus/p00a';D=R/'product-device'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):({'symlink':str(p.readlink())} if p.is_symlink() else {'sha256':sha(p)}) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
before=manifest(active);shutil.copytree(active,D,symlinks=True)
radio=R/'inputs/radio-userspace';shutil.copytree(radio,D/'radio')
patch=R/'inputs/0001-accept-asus-bt-container.patch'
assert sha(patch)=='0bdcc9b6f8beb148314c98ece4866c31dc27c9fe60a6d7321f68a21576093dfe'
subprocess.run(['git','apply','--check',str(patch)],cwd=D/'radio',check=True)
subprocess.run(['git','apply',str(patch)],cwd=D/'radio',check=True)
p=D/'device.mk';s=p.read_text();s+='\n$(call inherit-product, device/asus/p00a/connectivity/wifi-sta-trial.mk)\n$(call inherit-product, device/asus/p00a/radio/radio.mk)\n$(call inherit-product, device/asus/p00a/radio/bluetooth.mk)\n';p.write_text(s)
p=D/'BoardConfig.mk';s=p.read_text();s+='\ninclude device/asus/p00a/connectivity/BoardConfig-connectivity.mk\nBOARD_VENDOR_SEPOLICY_DIRS += device/asus/p00a/radio/sepolicy\nDEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml\n';p.write_text(s)
# BoardConfig owns manifest assignment after its base :=; avoid duplicate fragments.
p=D/'radio/bluetooth.mk';s=p.read_text();assert s.count('DEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml\n')==1;s=s.replace('DEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml\n','');p.write_text(s)
p=D/'rootdir/ueventd.rc';lines=p.read_text().splitlines();new=(D/'radio/ueventd.radio.rc.fragment').read_text();paths={x.split()[0] for x in new.splitlines() if x and not x.startswith('#')};lines=[x for x in lines if not x.split() or x.split()[0] not in paths];p.write_text('\n'.join(lines)+'\n\n'+new)
p=D/'radio/sepolicy/file_contexts';s=p.read_text().replace('/vendor/bin/p00a-wmt ', '/(vendor|system/vendor)/bin/p00a-wmt ');s+='/(vendor|system/vendor)/bin/hw/android\\.hardware\\.bluetooth@1\\.1-service\\.p00a u:object_r:hal_bluetooth_default_exec:s0\n';p.write_text(s)
wificond=A/'system/connectivity/wificond/wificond.rc';before_wificond=sha(wificond)
(R/'inputs/wificond-before.rc').write_bytes(wificond.read_bytes())
assert before==manifest(active),'Active source changed while staging'
after=manifest(D);changes={p:{'before':before.get(p),'after':v} for p,v in after.items() if before.get(p)!=v}
(R/'evidence/product-staging.json').write_text(json.dumps({'active':str(active),'candidate':str(D),'active_unchanged':True,'before':before,'changes':changes,'wificond_before_sha256':before_wificond,'wificond_after_sha256':sha(D/'radio/wificond.rc'),'calibration_uploaded':False},indent=2)+'\n')
print('Prepared',len(changes),'changed/new files; active product untouched')
