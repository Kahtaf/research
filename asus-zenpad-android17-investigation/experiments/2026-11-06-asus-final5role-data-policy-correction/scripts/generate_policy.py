import hashlib,json
from bounded import R,run
T=R/'tools/host';lib=T/'libsepol';A=R/'artifacts';I=R/'inputs'
run(['/usr/bin/clang','-O2','-Wno-incompatible-pointer-types-discards-qualifiers','-I'+str(lib/'include'),R/'baseline/source/policy_build.c',lib/'src/libsepol.a','-o',T/'baseline_policy_build'])
run([T/'baseline_policy_build',I/'base-policy',A/'reproduced-frozen-policy'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'reproduced-frozen-policy')==sha(I/'restore-sepolicy')=='16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2'
policies=[A/'UNQUALIFIED-future5role-policy',A/'UNQUALIFIED-future5role-policy-reproduction']
logs=[]
for p in policies:
    q=run([T/'policy_build',I/'base-policy',p]);logs.append(q.stdout)
    q=run([T/'policy_audit',I/'base-policy',p,I/'restore-sepolicy']);(R/'evidence'/(p.name+'-audit.json')).write_text(q.stdout)
assert policies[0].read_bytes()==policies[1].read_bytes() and logs[0]==logs[1]
(R/'evidence/reproduction.json').write_text(json.dumps(dict(passed=True,baseline_reproduced=True,baseline_sha256=sha(I/'restore-sepolicy'),future_sha256=sha(policies[0]),future_bytes=policies[0].stat().st_size,independent_output_files_equal=True,same_compiled_host_builder=True,full_clean_toolchain_rebuild_not_claimed=True,builder_emitted_rules=logs[0].splitlines()),indent=2)+'\n')
print('BASELINE_EXACT_AND_FUTURE_REPRODUCED',sha(policies[0]),policies[0].stat().st_size)
