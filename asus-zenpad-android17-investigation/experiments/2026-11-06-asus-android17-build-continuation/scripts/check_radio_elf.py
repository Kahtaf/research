#!/usr/bin/env python3
"""Run the actual strict SDK37 checker on exact ARM32 blobs and dependencies."""
import pathlib,subprocess,shutil,hashlib,json
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');O=R/'radio-elf-r1';O.mkdir();pins={};records=[]
def freeze(p,name):
    before=hashlib.sha256(p.read_bytes()).hexdigest();q=O/name;shutil.copyfile(p,q)
    assert before==hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(q.read_bytes()).hexdigest()
    pins[str(p)]=before;return q
checker=freeze(A/'build/make/tools/check_elf_file.py','check_elf_file.py')
inputs={
 'libc.so':A/'out/target/product/p00a/system/lib/bootstrap/libc.so',
 'libdl.so':A/'out/target/product/p00a/system/lib/bootstrap/libdl.so',
 'libc++.so':A/'out/target/product/p00a/system/vendor/lib/libc++.so',
 'libcutils.so':A/'out/soong/.intermediates/system/core/libcutils/libcutils/android_vendor_arm_armv8-a_cortex-a53_shared/libcutils.so',
 'liblog.so':A/'out/soong/.intermediates/system/logging/liblog/liblog/android_vendor_arm_armv8-a_cortex-a53_shared/liblog.so',
 'libm.so':A/'out/soong/.intermediates/bionic/libm/libm/android_vendor_arm_armv8-a_cortex-a53_shared/libm.so',
 'libbtcal.so':R/'btcal-arm32-r3/libbtcal.so',
 'libbluetooth_mtk.so':R/'product-device/radio/bluetooth/libbluetooth_mtk.so',
 'libbt-vendor.so':R/'product-device/radio/bluetooth/libbt-vendor.so',
}
for name,p in inputs.items():
    q=freeze(p,name);assert q.read_bytes()[:5]==b'\x7fELF\x01'
dependencies={
 'libbtcal.so':['libc.so'],
 'libbluetooth_mtk.so':['liblog.so','libcutils.so','libbtcal.so','libc++.so','libdl.so','libc.so','libm.so'],
 'libbt-vendor.so':['liblog.so','libbluetooth_mtk.so','libc++.so','libdl.so','libc.so','libm.so'],
}
for name,deps in dependencies.items():
    cmd=['python3',str(checker),'--llvm-readobj',str(A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readobj'),'--soname',name,'--max-page-size','4096']
    for dep in deps:cmd+=['--shared-lib',str(O/dep)]
    cmd.append(str(O/name));p=subprocess.run(cmd,capture_output=True)
    records.append({'argv':cmd,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()})
    (O/'results.json').write_text(json.dumps({'inputs':pins,'commands':records,'strict_checks_disabled':False,'final_soong_still_required':True},indent=2)+'\n')
    print(name,p.returncode,p.stderr.decode());assert p.returncode==0
