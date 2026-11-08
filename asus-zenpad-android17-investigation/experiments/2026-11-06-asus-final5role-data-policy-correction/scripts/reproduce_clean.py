import hashlib,json,tarfile
from bounded import R,run
out=R/'tools/clean-reproduction';out.mkdir();lib=out/'libsepol'
with tarfile.open(R/'inputs/libsepol-android-7.1.2_r39.tar.gz') as t:t.extractall(lib,filter='data')
run(['make','-C',lib/'src','libsepol.a','DISABLE_CIL=y','CC=/usr/bin/clang','CFLAGS=-O2 -Wno-error -DDARWIN -D_DARWIN_C_SOURCE','-j1'])
run(['/usr/bin/clang','-O2','-Wall','-Wextra','-Wno-incompatible-pointer-types-discards-qualifiers','-I'+str(lib/'include'),R/'source/policy_build.c',lib/'src/libsepol.a','-o',out/'policy_build'])
p=R/'artifacts/UNQUALIFIED-future5role-policy-clean-reproduction'
run([out/'policy_build',R/'inputs/base-policy',p])
run([R/'tools/host/policy_audit',R/'inputs/base-policy',p,R/'inputs/restore-sepolicy'])
assert p.read_bytes()==(R/'artifacts/UNQUALIFIED-future5role-policy').read_bytes()
(R/'evidence/clean-reproduction.json').write_text(json.dumps(dict(passed=True,new_library_extraction=True,new_serial_library_compilation=True,new_builder_compilation=True,binary_policy_equal=True,policy_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),compiler_host_same=True),indent=2)+'\n')
print('CLEAN_TOOLCHAIN_POLICY_REPRODUCTION_PASS')
