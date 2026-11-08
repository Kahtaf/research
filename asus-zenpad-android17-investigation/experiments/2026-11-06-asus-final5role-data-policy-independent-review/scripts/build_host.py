from pathlib import Path
import hashlib,json,tarfile
from bounded import R,run
out=R/'tools/host';out.mkdir()
lib=out/'libsepol'
with tarfile.open(R/'inputs/libsepol-android-7.1.2_r39.tar.gz') as t:t.extractall(lib,filter='data')
run(['make','-C',lib/'src','libsepol.a','DISABLE_CIL=y','CC=/usr/bin/clang','CFLAGS=-O2 -Wno-error -DDARWIN -D_DARWIN_C_SOURCE','-j1'])
for name in ['policy_build','policy_audit','policy_constraints','policy_query','policy_reachability','policy_xperms','mutate_policy']:
    src=R/('source' if name in ['policy_build','policy_audit'] else 'tests')/(name+'.c')
    run(['/usr/bin/clang','-O2','-Wall','-Wextra','-Wno-incompatible-pointer-types-discards-qualifiers','-I'+str(lib/'include'),src,lib/'src/libsepol.a','-o',out/name])
run(['/usr/bin/clang','--version'])
