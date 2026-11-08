from pathlib import Path
import subprocess as s, hashlib, json, difflib, os
R=Path('/srv/android/asus-firstboot-runtime'); T=Path('/srv/android/lineage24/kernel/asus/p00a-fd'); K=R/'kernel-cpuset-r1'; B=R/'kernel-build-r6'; S=R/'stagedpatches/cpuset-v2'; S.mkdir(); assert not K.exists() and not B.exists()
s.run(['cp','-a','--reflink=auto',str(R/'kernel'),str(K)],check=True)
paths=['include/linux/cgroup-defs.h','kernel/cgroup.c','kernel/cpuset.c']; before={p:(K/p).read_text() for p in paths}
for p in paths: assert (T/p).read_bytes()==(K/p).read_bytes(), ('physical baseline differs',p)
p=K/paths[0]; text=p.read_text(); needle='\tCGRP_ROOT_XATTR\t\t= (1 << 2), /* supports extended attributes */'; assert text.count(needle)==1;p.write_text(text.replace(needle,needle+'\n\t/* Enable cpuset v2 behavior on a v1 hierarchy. */\n\tCGRP_ROOT_CPUSET_V2_MODE = (1 << 4),'))
p=K/paths[1];text=p.read_text();needle='\tif (root->flags & CGRP_ROOT_XATTR)\n\t\tseq_puts(seq, ",xattr");';assert text.count(needle)==1;text=text.replace(needle,needle+'\n\tif (root->flags & CGRP_ROOT_CPUSET_V2_MODE)\n\t\tseq_puts(seq, ",cpuset_v2_mode");');needle='\t\tif (!strcmp(token, "xattr")) {';assert text.count(needle)==1;text=text.replace(needle,'\t\tif (!strcmp(token, "cpuset_v2_mode")) {\n\t\t\topts->flags |= CGRP_ROOT_CPUSET_V2_MODE;\n\t\t\tcontinue;\n\t\t}\n'+needle);p.write_text(text)
p=K/paths[2];text=p.read_text();assert text.count('cgroup_subsys_on_dfl(cpuset_cgrp_subsys)')==10;text=text.replace('cgroup_subsys_on_dfl(cpuset_cgrp_subsys)','is_in_v2_mode()');needle='static DECLARE_WAIT_QUEUE_HEAD(cpuset_attach_wq);';assert text.count(needle)==1;text=text.replace(needle,needle+'''

/* Cached at bind time; do not dereference a potentially stale root here. */
static bool cpuset_v2_mode;

static inline bool is_in_v2_mode(void)
{
	return cgroup_subsys_on_dfl(cpuset_cgrp_subsys) ||
	       READ_ONCE(cpuset_v2_mode);
}
''');needle='static void cpuset_bind(struct cgroup_subsys_state *root_css)\n{\n\tmutex_lock(&cpuset_mutex);\n\tspin_lock_irq(&callback_lock);\n';assert text.count(needle)==1;text=text.replace(needle,needle+'\n\tWRITE_ONCE(cpuset_v2_mode,\n\t\t   !!(cpuset_cgrp_subsys.root->flags & CGRP_ROOT_CPUSET_V2_MODE));\n');p.write_text(text)
patch='';manifest=[]
for p in paths:
 after=(K/p).read_text();patch+=''.join(difflib.unified_diff(before[p].splitlines(True),after.splitlines(True),fromfile='a/'+p,tofile='b/'+p));manifest.append(dict(path=p,before_sha256=hashlib.sha256(before[p].encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
(S/'0002-cpuset-v2-mode-backport.patch').write_text(patch);(S/'manifest.json').write_text(json.dumps(dict(files=manifest,upstream=['e1cba4b85daa71b710384d451ff6238d5e4d1ff6','b8d1b8ee93df8ffbabbeadd65d39853cfad6d698','e06b678e3b4e12fdaa0b51a7a5a54abc5dbd6469'],scope='Real cpuset v2 semantics, mount-option parse/display, cached bind flag; no userspace fallback or readiness manipulation',active_source_edited=False),indent=2))
s.run(['cp','-a','--reflink=auto',str(R/'kernel-build-r5'),str(B)],check=True)
# Rebind the copied output wrapper to the copied source, leaving r5 immutable.
args=['make','-C',str(K),'O='+str(B),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','KBUILD_BUILD_USER=asus-port','KBUILD_BUILD_HOST=firstboot-runtime','KBUILD_BUILD_VERSION=1','KBUILD_BUILD_TIMESTAMP=Fri Nov 6 00:00:00 UTC 2026'];os.environ['TMPDIR']=str(R/'tmp')
(R/'evidence/kernel-cpuset-command.json').write_text(json.dumps(args+['-j1','Image'],indent=2));p=s.run(args+['-j1','Image']);(R/'evidence/kernel-cpuset-status.json').write_text(json.dumps(dict(returncode=p.returncode)));assert p.returncode==0
(R/'evidence/kernel-cpuset-hashes.json').write_text(json.dumps({str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B/'.config',B/'arch/arm64/boot/Image']},indent=2))
