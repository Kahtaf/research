from pathlib import Path
import subprocess as s,json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');tool='/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readelf'
for n in ['bpfloader','libbpf_android.so','libbpf_android.candidate.so']:
 print(n,s.run([tool,'-d','-s',str(R/'inputs'/n)],capture_output=True,text=True).stdout[:8500])
f=json.loads((R/'inputs/trace-files.json').read_text());print('LIBS',[(n,v) for n,v in f.items() if 'bpf_android' in n])
