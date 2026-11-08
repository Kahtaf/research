from pathlib import Path
import os
os.makedirs("/srv/android/asus-network-runtime/tmp",exist_ok=True)
os.environ["TMPDIR"]="/srv/android/asus-network-runtime/tmp"
import subprocess as s,json,hashlib,sys,shutil,difflib,struct
R=Path('/srv/android/asus-network-runtime');I=R/'inputs';H=I/'headers';C=Path('/srv/android/lineage24/prebuilts/clang/host/linux-x86/clang-r584948b');B=I/'Connectivity/bpf/progs';O=R/'artifacts'/('bpf-'+sys.argv[1]);O.mkdir()
source=R/'staged-network/bpf/progs' if sys.argv[1]=='network' else B
if sys.argv[1]=='core':
 source=R/'staged-core-progs';shutil.copytree(B,source)
 p=source/'netd.c';old=p.read_text();new=old
 for direction in ['ingress','egress']:
  marker='// ----- '+('egress/stats -----' if direction=='ingress' else '\n\n// WARNING: Android T\'s non-updatable netd depends on the name of this program.')
  section=f'''// Local legacy path: retain UID firewall, VPN ingress filtering and accounting.
// Newer local-network/loopback features require separately qualified helpers.
DEFINE_NETD_BPF_PROG_RANGES({direction}, stats, 4_9, 4_14, V, MAXAPI)
(struct __sk_buff* skb) {{
    return bpf_traffic_account(skb, {direction.upper()}, KVER_4_9, API(T));
}}

'''
  if direction=='ingress':new=new.replace('// ----- egress/stats -----',section+'// ----- egress/stats -----')
  else:new=new.replace('// WARNING: Android T\'s non-updatable netd depends on the name of this program.\nDEFINE_XTBPF_PROG(skfilter, egress_xtbpf)',section+'// WARNING: Android T\'s non-updatable netd depends on the name of this program.\nDEFINE_XTBPF_PROG(skfilter, egress_xtbpf)')
 p.write_text(new);(R/'patches/10-core-cgroup-programs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/bpf/progs/netd.c',tofile='b/bpf/progs/netd.c')))
for name in (['netd'] if sys.argv[1] in ('core','network') else ['netd','offload','test','clatd','dscpPolicy']):
 cmd=[str(C/'bin/clang'),'--target=bpf','-mcpu=v1','-c','-nostdlibinc','-no-canonical-prefixes','-O2','-Wall','-Werror','-Wextra']
 for p in [H/'bionic/libc/include',H/'bionic/libc/kernel/uapi',H/'bionic/libc/kernel/uapi/asm-arm64',H/'bionic/libc/kernel/android/uapi']:cmd+=['-isystem',str(p)]
 for p in [I/'extra/system/core/libcutils/include',I/'netd-include/mainline',source,source/'include']:cmd+=['-I',str(p)]
 cmd+=['-g','-fdebug-prefix-map='+str(R)+'=','-MD','-MF',str(O/(name+'.d')),'-o',str(O/(name+'.unstripped.o')),str(source/(name+'.c'))]
 r=s.run(cmd,capture_output=True,text=True);(O/(name+'.build.json')).write_text(json.dumps(dict(command=cmd,exit=r.returncode,output=r.stdout+r.stderr),indent=2)+'\n');print(name,r.returncode,r.stderr);assert r.returncode==0
 s.run([str(C/'bin/llvm-strip'),'-g',str(O/(name+'.unstripped.o')),'-o',str(O/(name+'.o'))],check=True)
def sections(p):
 d=p.read_bytes();shoff=struct.unpack_from('<Q',d,40)[0];entsize,count,stridx=struct.unpack_from('<HHH',d,58);sh=[struct.unpack_from('<IIQQQQIIQQ',d,shoff+i*entsize) for i in range(count)];strings=d[sh[stridx][4]:sh[stridx][4]+sh[stridx][5]];out={}
 for h in sh:
  name=strings[h[0]:].split(b'\0')[0].decode();
  if h[2]&2 or h[1] in (9,):out[name]=hashlib.sha256(d[h[4]:h[4]+h[5]]).hexdigest()
 return out
if sys.argv[1]=='original':
 a=sections(I/'root/apex/com.android.tethering/etc/bpf/mainline/netd.o');b=sections(O/'netd.o');(R/'evidence/netd-object-source-match.json').write_text(json.dumps(dict(equal=a==b,captured=a,rebuilt=b),indent=2)+'\n');print('netd original allocated/code/relocation sections match:',a==b)
