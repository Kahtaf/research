from pathlib import Path
import subprocess as s,re,json,hashlib,shutil
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24');P=T/'out/target/product/p00a';O=R/'inputs/platform-root';O.mkdir(exist_ok=True);manifest={}
def put(src,dest):
 data=src.read_bytes();assert hashlib.sha256(data).digest()==hashlib.sha256(src.read_bytes()).digest(),src
 out=O/dest;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);manifest[dest]={'source':str(src),'sha256':hashlib.sha256(data).hexdigest()};return out
root=put(R/'inputs/platform-bpfloader','system/bin/bpfloader');queue=[root];seen=set()
while queue:
 f=queue.pop();dynamic=s.check_output(['aarch64-linux-gnu-readelf','-d',str(f)],text=True)
 for name in re.findall(r'Shared library: \[(.*?)\]',dynamic):
  if name in seen:continue
  seen.add(name)
  candidates=[P/'system/lib64'/name,R/'inputs/root/system/lib64'/name]
  known={'libaconfig_storage_protos.dylib.so':'build/make/tools/aconfig/aconfig_storage_file/libaconfig_storage_protos/android_arm64_armv8-a_dylib','libvsprintf_wrapper.so':'external/rust/android-crates-io/crates/vsprintf/libvsprintf_wrapper/android_arm64_armv8-a_shared','libandroid_bpfprogs_flags.dylib.so':'system/bpfprogs/libandroid_bpfprogs_flags/android_arm64_armv8-a_dylib','librustutils.dylib.so':'system/librustutils/rustutils/librustutils/android_arm64_armv8-a_dylib','liblibbpf_rs.dylib.so':'external/rust/android-crates-io/crates/libbpf-rs/liblibbpf_rs/android_arm64_armv8-a_dylib','libbpf_android.so':'system/bpf/loader/libbpf_android/android_arm64_armv8-a_shared'}
  if name.startswith('libaconfig_'):
   module=name.split('.')[0];crate=module[3:];candidates.append(T/'out/soong/.intermediates/build/make/tools/aconfig'/crate/module/'android_arm64_armv8-a_dylib'/name)
  module=name.split('.')[0];crate=module.removeprefix('lib')
  for dirname in {crate,crate.replace('_','-')}:candidates.append(T/'out/soong/.intermediates/external/rust/android-crates-io/crates'/dirname/module/'android_arm64_armv8-a_dylib'/name)
  if name in known:candidates.append(T/'out/soong/.intermediates'/known[name]/name)
  found=next((x for x in candidates if x.is_file()),None)
  if found is None:raise RuntimeError('missing '+name)
  queue.append(put(found,'system/lib64/'+name))
for f in (P/'system/etc/bpf').rglob('*'):
 if f.is_file():put(f,str(f.relative_to(P)))
(R/'evidence/platform-capture.json').write_text(json.dumps(manifest,indent=2)+'\n');print('captured files',len(manifest))
