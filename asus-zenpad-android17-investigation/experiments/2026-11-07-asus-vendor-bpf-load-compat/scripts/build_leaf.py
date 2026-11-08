from pathlib import Path
import re,json,shlex,subprocess as s,hashlib,difflib,os
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');os.environ['TMPDIR']=str(R/'tmp');E=R/'evidence';V={}
def logical(f):
 acc=''
 for l in f:
  acc+=l
  if l.rstrip().endswith('$'):acc=acc.rstrip()[:-1];continue
  yield acc.rstrip('\n');acc=''
with (A/'out/soong/build.lineage_p00a.ninja').open() as f:
 for l in logical(f):
  if l.startswith('build '):break
  m=re.match(r'^([\w.\-]+) = (.*)$',l)
  if m:V[m[1]]=m[2]
edges=json.loads((E/'native-edges.json').read_text());text='\n'.join(edges)
for l in text.splitlines():
 m=re.match(r'^([\w.\-]+) = (.*)$',l)
 if m:V[m[1]]=m[2]
def expand(x):
 for _ in range(25):
  y=re.sub(r'\$\{([^}]+)\}',lambda m:V[m[1]],x)
  if y==x:return y
  x=y
 raise RuntimeError('recursive vars')
pre=A/'system/bpf/loader/Loader.cpp';source=pre.read_text();old='            strlcpy(req.prog_name, cs[i].name.c_str(), sizeof(req.prog_name));';assert source.count(old)==1;post=source.replace(old,'            if (isAtLeastKernelVersion(4, 15))\n    '+old);(R/'source/Loader.pre.cpp').write_text(source);(R/'source/Loader.cpp').write_text(post);(R/'source/loader-prog-name.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),post.splitlines(True),fromfile='a/system/bpf/loader/Loader.cpp',tofile='b/system/bpf/loader/Loader.cpp')))
# Preserve source-relative public header resolution in the isolated source copy.
(R/'source/include').mkdir(exist_ok=True);(R/'source/include/libbpf_android.h').write_bytes((pre.parent/'include/libbpf_android.h').read_bytes())
clang=expand('${g.android.soong.cc.config.ClangBin}')+'/clang++';flags=shlex.split(expand('${m.libbpf_android_android_arm64_armv8-a_static.cFlags1}'))
obj=R/'inputs/Loader.o';cmd=[clang,*flags,'-MD','-MF',str(R/'inputs/Loader.d'),'-c',str(R/'source/Loader.cpp'),'-o',str(obj)];commands=[]
def run(cmd):
 p=s.run(cmd,cwd=A,env=os.environ,capture_output=True,text=True);commands.append(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(E/'leaf-build.json').write_text(json.dumps(commands,indent=2));print('BUILD',p.returncode,p.stderr[-1500:],flush=True);assert p.returncode==0
run(cmd)
edge=next(x for x in edges if '    ldFlags = ' in x);settings={}
for l in edge.splitlines():
 m=re.match(r'    (\w+) = (.*)',l)
 if m:settings[m[1]]=m[2]
ldflags=shlex.split(expand(settings['ldFlags']));crt=shlex.split(settings['crtBegin']);end=shlex.split(settings['crtEnd']);libs=shlex.split(settings['libFlags']);out=R/'inputs/libbpf_android.unstripped.so';run([clang,*ldflags,*crt,str(obj),*libs,*end,'-Wl,--build-id=md5','-o',str(out)])
strip=expand('${g.android.soong.cc.config.ClangBin}')+'/llvm-strip';run([strip,'--strip-debug',str(out),'-o',str(R/'inputs/libbpf_android.candidate.so')])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();d=dict(source_origin=str(pre),pre_sha256=sha(R/'source/Loader.pre.cpp'),post_sha256=sha(R/'source/Loader.cpp'),source_origin_unchanged=pre.read_text()==source,patch_sha256=sha(R/'source/loader-prog-name.patch'),candidate_sha256=sha(R/'inputs/libbpf_android.candidate.so'),unstripped_sha256=sha(out),object_sha256=sha(obj),compiler_sha256=sha(A/clang),strip_sha256=sha(A/strip),installed_pre_sha256=sha(R/'inputs/libbpf_android.so'),kernel_unchanged=True)
(E/'leaf-identity.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
