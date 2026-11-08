#!/usr/bin/env python3
"""Exercise final-image byte checking with real small host ext4 filesystems."""
import hashlib,json,pathlib,shutil,subprocess,sys
from verify_google_payload import verify

root=pathlib.Path(sys.argv[1]);root.mkdir();product=root/'product';product.mkdir();manifest={'zip':{'synthetic_test_fixture':True},'payload_members':{}}
paths=['system/product/priv-app/Phonesky/Phonesky.apk','system/system_ext/priv-app/GoogleServicesFramework/GoogleServicesFramework.apk','system/product/apex/com.google.android.gmssystem.prodvic.apex','system/system_ext/priv-app/SetupWizard/SetupWizard.apk']
for i,name in enumerate(paths):
    data=('synthetic signed-payload byte test '+str(i)).encode();p=product/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);manifest['payload_members'][name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
debugfs=pathlib.Path(shutil.which('debugfs') or '/usr/sbin/debugfs');mke2fs=shutil.which('mke2fs') or '/usr/sbin/mke2fs';results={}
def make_image(name,source):
    p=root/name
    with p.open('xb') as f:f.truncate(16*1024*1024)
    subprocess.run([mke2fs,'-q','-F','-t','ext4','-d',str(source),str(p)],check=True,capture_output=True)
    return p
image=make_image('valid.ext4',product);verify(manifest,product,image,debugfs);results['actual_ext4_correct_bytes']=True
flat=make_image('wrong-layout.ext4',product/'system')
try:verify(manifest,product,flat,debugfs)
except AssertionError:results['wrong_flat_system_layout_rejected']=True
else:raise AssertionError('Wrong system image layout accepted')
target=product/paths[0];original=target.read_bytes();target.write_bytes(original[:-1]+b'X')
try:verify(manifest,product,image,debugfs)
except AssertionError:results['altered_staged_byte_rejected']=True
else:raise AssertionError('Altered staged byte accepted')
bad=make_image('wrong.ext4',product);target.write_bytes(original)
try:verify(manifest,product,bad,debugfs)
except AssertionError:results['altered_final_ext4_byte_rejected']=True
else:raise AssertionError('Altered image byte accepted')
target.unlink();target.symlink_to(image)
try:verify(manifest,product,image,debugfs)
except AssertionError:results['staged_symlink_rejected']=True
else:raise AssertionError('Staged symlink accepted')
(root/'results.json').write_text(json.dumps({'synthetic_test_fixture':True,'tests':results},indent=2)+'\n');print(results)
