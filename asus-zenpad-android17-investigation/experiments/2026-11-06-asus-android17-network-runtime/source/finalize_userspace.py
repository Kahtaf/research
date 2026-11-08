from pathlib import Path
import difflib
R=Path('/srv/android/asus-network-runtime');S=R/'staged-network';I=R/'inputs/Connectivity'
p=S/'bpf/loader/NetBpfLoad.cpp';s=p.read_text().replace('// Local: on legacy (pre-4.14) kernels with ro.bpf.allow_legacy_kernel, log\n// and skip objects the kernel rejects instead of failing the whole boot.','// The opt-in legacy product uses the ELF loader and qualified kernel backports.')
s=s.replace('if (!isAtLeastKernelVersion(4, 14)) return true;', 'if (!isAtLeastKernelVersion(4, 14) &&\n        !GetBoolProperty("ro.bpf.allow_legacy_kernel", false)) return true;')
p.write_text(s)
p=S/'bpf/netd/BpfHandler.cpp';s=p.read_text();a=s.index('    // Local: on legacy kernels the A17 cgroup');b=s.index('\n    // For the devices',a);s=s[:a]+'''    // These programs enforce UID firewall and VPN ingress policy as well as accounting.
    RETURN_IF_NOT_OK(attachProgramToCgroup(BPF_EGRESS_PROG_PATH, cg_fd, BPF_CGROUP_INET_EGRESS));
    RETURN_IF_NOT_OK(attachProgramToCgroup(BPF_INGRESS_PROG_PATH, cg_fd, BPF_CGROUP_INET_INGRESS));
''' + s[b:];p.write_text(s)
files=['bpf/loader/NetBpfLoad.cpp','bpf/netd/BpfHandler.cpp','bpf/progs/netd.c'];patch=''
for f in files:patch+=''.join(difflib.unified_diff((I/f).read_text().splitlines(True),(S/f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(R/'patches/11-network-policy-and-required-loader.patch').write_text(patch)
