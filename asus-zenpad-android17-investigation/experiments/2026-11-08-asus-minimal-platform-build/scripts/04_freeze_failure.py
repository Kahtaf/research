from pathlib import Path
import base64,hashlib,json,re
R=Path('/srv/android/asus-minimal-platform-build-20261108');K=R/'kernel';P=Path('/srv/android/asus-minimal-platform-preparation-20261108');B=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107');E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=K/'drivers/misc/mediatek/devapc/mt8163/devapc.c'
# Collect only the failing translation unit and its local declaration header.
paths=[src,src.with_suffix('.h')];files={}
for p in paths:
 if p.is_file():
  d=p.read_bytes();files['evidence/failure-source/'+p.name]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
prepared=json.loads((P/'evidence/preparation-receipt.json').read_text())
for n,h in prepared['uploaded'].items():assert sha(P/n)==h,n
for n,h in prepared['baseline_selected_unchanged'].items():assert sha(P/'kernel'/n)==h,n
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb'
assert sha(B/'out/.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
record=dict(status='STOPPED_ON_FIRST_KERNEL_COMPILE_FAILURE',helper_compile_attempts=1,kernel_build_attempts=1,no_retry=True,prepared_source_and_inputs_unchanged=True,calibrated_ancestor_image_and_config_unchanged=True,partial_out_preserved=str(R/'out'),no_final_Image_or_vmlinux=True,no_System_map_claim=True,no_candidate_or_package=True,no_PLAN_or_trial=True,no_new_stubs_config_variants_or_guard_weakening=True)
(E/'stop-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
d=(E/'stop-receipt.json').read_bytes();files['evidence/stop-receipt.json']=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,**record)))
