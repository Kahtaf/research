from pathlib import Path
import json,hashlib
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');A=Path('/srv/android/lineage24');S=R/'source/reference';S.mkdir(exist_ok=True);d={}
for label,p in [('kernel-syscall.c',R/'kernel/kernel/bpf/syscall.c'),('kernel-bpf.h',R/'kernel/include/uapi/linux/bpf.h'),('KernelUtils.h',A/'packages/modules/Connectivity/bpf/headers/include/bpf/KernelUtils.h'),('NetBpfLoad.cpp',A/'packages/modules/Connectivity/bpf/loader/NetBpfLoad.cpp')]:
 b=p.read_bytes();(S/label).write_bytes(b);d[label]=dict(origin=str(p),sha256=hashlib.sha256(b).hexdigest())
(R/'evidence/reference-sources.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
