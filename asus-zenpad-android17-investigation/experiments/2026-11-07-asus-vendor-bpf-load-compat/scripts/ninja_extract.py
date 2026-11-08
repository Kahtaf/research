from pathlib import Path
import json
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107')
p=A/'out/soong/build.lineage_p00a.ninja';print('exists',p.exists())
selected=[]
with p.open() as f:
 keep=False
 for line in f:
  if line.startswith('build '):keep=('system/bpf/loader/libbpf_android/android_arm64_armv8-a_shared/' in line)
  if keep:selected.append(line)
(R/'evidence/ninja-edges.txt').write_text(''.join(selected));print(''.join(selected)[:21000])
p=A/'out/soong/.intermediates/system/bpf/loader/libbpf_android/android_arm64_armv8-a_shared/unstripped/libbpf_android.so.rsp';print('RSP',p.read_text()[:5000])
