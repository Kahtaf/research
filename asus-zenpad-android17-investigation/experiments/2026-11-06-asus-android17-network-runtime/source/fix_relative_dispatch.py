from pathlib import Path
import difflib
R=Path('/srv/android/asus-network-runtime');p=R/'kernel/net/core/filter.c';s=p.read_text();a=s.index('cg_skb_func_proto(');b=s.index('\tcase BPF_FUNC_skb_load_bytes:',a);s=s[:b]+'\tcase BPF_FUNC_skb_load_bytes_relative:\n\t\treturn &bpf_skb_load_bytes_relative_proto;\n'+s[b:];p.write_text(s)
# Replace the proposal with the cumulative patch against its original baseline.
base=(R/'inputs/filter-baseline.c').read_text();header_old=(R/'staged-lpm/include/uapi/linux/bpf.h').read_text();header=(R/'kernel/include/uapi/linux/bpf.h').read_text();(R/'patches/03-skb-relative-load.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),s.splitlines(True),fromfile='a/net/core/filter.c',tofile='b/net/core/filter.c'))+''.join(difflib.unified_diff(header_old.splitlines(True),header.splitlines(True),fromfile='a/include/uapi/linux/bpf.h',tofile='b/include/uapi/linux/bpf.h')))
