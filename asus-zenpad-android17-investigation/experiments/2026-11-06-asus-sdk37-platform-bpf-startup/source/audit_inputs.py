from pathlib import Path
import subprocess as s,hashlib,json
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24')
for p in [T/'system/bpf/loader/bpfloader.rs',R/'inputs/platform-source/bpfloader.rs',R/'platform-build-legacy/bpfloader.rs',R/'patches/12-platform-ringbuf-selftest-minimum.patch',R/'artifacts/bpfloader-legacy']:
 print('HASH',hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size,p)
for p in [R/'inputs/platform-source/bpfloader.rs',R/'platform-build-legacy/bpfloader.clang.rsp',R/'platform-build-legacy/bpfloader.d.raw',R/'source/guest_init.c',R/'source/seed_properties.cpp',R/'run-r16/serial.log']:
 print('FILE',p);print(p.read_text())
print('GRAPH FILES');print(s.run(['find','out','-maxdepth','2','-name','*.ninja'],cwd=T,capture_output=True,text=True).stdout)
for p in [T/'system/bpfprogs/Android.bp',T/'system/bpf/loader/Android.bp']:
 print('FILE',p);print(p.read_text())
print('PRODUCT INSTALL GRAPH MATCHES')
for p in [T/'out/build-lineage_p00a.ninja',T/'out/soong/build.ninja']:
 if p.exists():
  for line in p.open():
   if line.startswith('build out/target/product/p00a/') and '/etc/bpf/' in line.split(':')[0]:print(line.rstrip())
