import tarfile
from bounded import R,run
out=R/'tools/host';pc=out/'pcre';sel=out/'libselinux'
for n,dest in [('pcre',pc),('libselinux',sel)]:
    with tarfile.open(R/'inputs'/(n+'-android-7.1.2_r39.tar.gz')) as t:t.extractall(dest,filter='data')
names=['byte_order','compile','config','dfa_exec','exec','fullinfo','get','globals','jit_compile','maketables','newline','ord2utf8','refcount','string_utils','study','tables','ucd','valid_utf8','version','xclass']
objs=[]
for src in [pc/'pcre_chartables.c']+[pc/'dist'/('pcre_'+n+'.c') for n in names]:
    obj=out/(src.stem+'.o');run(['/usr/bin/clang','-O2','-DHAVE_CONFIG_H','-I'+str(pc),'-I'+str(pc/'dist'),'-c',src,'-o',obj]);objs.append(obj)
run(['/usr/bin/ar','rcs',out/'libpcre.a',*objs])
host=['callbacks','check_context','freecon','init','label','label_file','label_android_property','label_support']
run(['/usr/bin/clang','-O2','-DHOST','-DDARWIN','-D_DARWIN_C_SOURCE','-D_GNU_SOURCE','-I'+str(pc),'-I'+str(sel/'include'),R/'tests/context_lookup.c',*[sel/'src'/(n+'.c') for n in host],out/'libpcre.a','-o',out/'context_lookup'])
