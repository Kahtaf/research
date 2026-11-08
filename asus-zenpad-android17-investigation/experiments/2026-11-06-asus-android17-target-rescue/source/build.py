"""Reproducible isolated build. This command never mutates main platform/kernel trees."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,tarfile
R=Path(__file__).resolve().parents[1];S=R/'source'
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
 if R!=Path('/srv/android/asus-target-rescue') or not out.is_relative_to(R):raise ValueError('build only in owned remote fixture')
 out.mkdir(parents=True,exist_ok=False);tmp=out/'tmp';tmp.mkdir();os.environ['TMPDIR']=str(tmp);os.environ['LC_ALL']='C';os.environ['SOURCE_DATE_EPOCH']='1793923200'
 log=[]
 def run(cmd):
  q=subprocess.run([str(c) for c in cmd],capture_output=True,text=True);log.append(dict(argv=[str(c) for c in cmd],returncode=q.returncode,stdout=q.stdout,stderr=q.stderr));(out/'commands.json').write_text(json.dumps(log,indent=2)+'\n')
  if q.returncode:raise RuntimeError(q.stderr[-4000:])
 arc=S/'libsepol-android-7.1.2_r39.tar.gz'
 assert hashlib.sha256(arc.read_bytes()).hexdigest()=='c17c444d73f1080a8959cfda2d4bdb529efd88f5af58a9e571917f473f83ff27'
 lib=out/'libsepol'
 with tarfile.open(arc) as t:t.extractall(lib,filter='data')
 run(['make','-C',lib/'src','libsepol.a','DISABLE_CIL=y','CC=gcc','CFLAGS=-O2 -Wno-error','-j2'])
 for n in ['policy_build','policy_constraints','policy_query','policy_inspect']:
  run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(lib/'include'),S/(n+'.c'),lib/'src/libsepol.a','-o',out/n])
 flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none']
 for n,src in [('os-rescue','rescue.c'),('rescue-proxy','proxy.c')]:
  run(['aarch64-linux-gnu-gcc',*flags,S/src,'-o',out/n])
  run(['aarch64-linux-gnu-readelf','-h','-l','-n',out/n])
 # Android 7 stock init opens compiled contexts and requires its PCRE version.
 pc=out/'pcre';sel=out/'libselinux'
 for name,dest,digest in [('pcre-android-7.1.2_r39.tar.gz',pc,'fb5d81e0e32b5047b2095ca865c75690aba079d5c8cb28497362deda95ab4947'),('libselinux-android-7.1.2_r39.tar.gz',sel,'8a8b5ef512bd4aa7ac8cdb8e1f7f64644ad340d75f5280f77c9c912d53970b9b')]:
  archive=S/name;assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest
  with tarfile.open(archive) as t:t.extractall(dest,filter='data')
 names=['byte_order','compile','config','dfa_exec','exec','fullinfo','get','globals','jit_compile','maketables','newline','ord2utf8','refcount','string_utils','study','tables','ucd','valid_utf8','version','xclass']
 objs=[]
 for src in [pc/'pcre_chartables.c']+[pc/'dist'/('pcre_'+n+'.c') for n in names]:
  obj=out/(src.stem+'.o');run(['gcc','-O2','-DHAVE_CONFIG_H','-I'+str(pc),'-I'+str(pc/'dist'),'-c',src,'-o',obj]);objs.append(obj)
 run(['ar','rcs',out/'libpcre.a',*objs])
 host=['callbacks','check_context','freecon','init','label','label_file','label_android_property','label_support']
 run(['gcc','-O2','-DHOST','-D_GNU_SOURCE','-I'+str(pc),'-I'+str(sel/'include'),sel/'utils/sefcontext_compile.c',*[sel/'src'/(n+'.c') for n in host],out/'libpcre.a','-o',out/'sefcontext_compile'])
 run(['gcc','-O2','-DHOST','-D_GNU_SOURCE','-I'+str(pc),'-I'+str(sel/'include'),S/'context_lookup.c',*[sel/'src'/(n+'.c') for n in host],out/'libpcre.a','-o',out/'context_lookup'])
 run(['aarch64-linux-gnu-gcc','--version']);run(['gcc','--version'])
 (out/'hashes.json').write_text(json.dumps({n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['os-rescue','rescue-proxy','policy_build','policy_constraints','policy_query','policy_inspect','sefcontext_compile','context_lookup']},indent=2)+'\n')
if __name__=='__main__':main()
