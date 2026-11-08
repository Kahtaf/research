from pathlib import Path
import subprocess as s
for path,start,stop in [('/srv/android/lineage24/system/bpf/loader/Loader.cpp',430,495),('/srv/android/lineage24/packages/modules/Connectivity/bpf/loader/NetBpfLoad.cpp',1055,1080),('/srv/android/lineage24/packages/modules/Connectivity/bpf/syscall_wrappers/include/BpfSyscallWrappers.h',40,110)]:
 print(path);print('\n'.join(Path(path).read_text().splitlines()[start-1:stop]))
p=Path('/srv/android/asus-final-bpf-runtime-20261106');print(s.run(['find',str(p),'-maxdepth','3','-type','f'],text=True,capture_output=True).stdout[:11000])
