from pathlib import Path
import json,subprocess as s
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');p=R/'evidence/native-commands.json';print('commands_exists',p.exists())
if p.exists(): print(p.read_text()[-18000:])
for p in [Path('/srv/android/asus-network-runtime/source/loader_probe.cpp'),Path('/srv/android/lineage24/system/bpf/loader/include/libbpf_android.h')]:
 if p.exists():print(p,p.read_text()[:6500])
print(s.run(['find','/srv/android/lineage24/out/soong/.intermediates/system/bpf/loader/libbpf_android','-maxdepth','3','-type','f'],capture_output=True,text=True).stdout[:3000])
