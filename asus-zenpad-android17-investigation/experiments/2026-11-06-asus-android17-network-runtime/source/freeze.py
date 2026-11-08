from pathlib import Path
import subprocess as s,hashlib,json,shutil
R=Path('/srv/android/asus-network-runtime'); T=Path('/srv/android/lineage24'); P=Path('/srv/android/asus-android17-runtime-prereqs')
manifest=[]
def copy(src,dst):
 a=src.read_bytes(); b=src.read_bytes(); assert a==b,src
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(a)
 manifest.append(dict(source=str(src),destination=str(dst.relative_to(R)),bytes=len(a),sha256=hashlib.sha256(a).hexdigest()))
C=T/'packages/modules/Connectivity'
for p in C.rglob('*'):
 if p.is_file() and '.git' not in p.parts: copy(p,R/'inputs/Connectivity'/p.relative_to(C))
for p in (P/'inputs/root').rglob('*'):
 if p.is_file():copy(p,R/'inputs/root'/p.relative_to(P/'inputs/root'))
for n in ['crtbegin_dynamic.o','crtend_android.o']:copy(P/'inputs'/n,R/'inputs'/n)
shutil.copytree(P/'inputs/headers',R/'inputs/headers',dirs_exist_ok=True)
copy(P/'build-r4/arch/arm64/boot/Image',R/'inputs/baseline.Image');copy(P/'build-r4/.config',R/'inputs/baseline.config')
copy(Path('/srv/android/asus-android17/bpf-fd-result/kernel.config'),R/'inputs/physical.config')
I=T/'out/soong/.intermediates/packages/modules/Connectivity'
for p in (I/'bpf/progs').glob('*/android_common/obj/packages/modules/Connectivity/bpf/progs/*.o'):
 copy(p,R/'inputs/root/apex/com.android.tethering/etc/bpf/mainline'/p.name)
copy(I/'bpf/loader/netbpfload/android_arm64_armv8-a_apex31/netbpfload',R/'inputs/root/system/bin/netbpfload')
copy(Path('/srv/android/asus-device-product/network-result/netd'),R/'inputs/root/system/bin/netd')
# Capture original active source identity and diffs independently of historical STATUS.
(R/'evidence/connectivity-head.txt').write_text(s.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True))
(R/'evidence/connectivity-active.diff').write_bytes(s.check_output(['git','-C',str(C),'diff','HEAD']))
(R/'evidence/frozen-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('frozen',len(manifest))
