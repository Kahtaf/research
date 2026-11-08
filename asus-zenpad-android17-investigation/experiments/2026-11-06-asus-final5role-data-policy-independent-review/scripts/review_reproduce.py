from bounded import R,run
import hashlib,json,shutil,os,runpy
T=R/'tools/host';I=R/'inputs';A=R/'artifacts';lib=T/'libsepol'
run(['/usr/bin/clang','-O2','-Wall','-I'+str(lib/'include'),R/'baseline/source/policy_build.c',lib/'src/libsepol.a','-o',T/'baseline_build'])
outputs={}
for tool,name,expect in [('baseline_build','reproduced-frozen','16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2'),('policy_build','UNQUALIFIED-future5role-policy','3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815'),('policy_build','UNQUALIFIED-repeat-policy','3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815')]:
 
 if not (A/name).exists():run([T/tool,I/'base-policy',A/name],timeout=10)
 data=(A/name).read_bytes();h=hashlib.sha256(data).hexdigest();assert h==expect;outputs[name]=dict(bytes=len(data),sha256=h)
q=run([T/'policy_audit',I/'base-policy',I/'reviewed-policy',I/'restore-sepolicy'],timeout=10)
qf=run([T/'policy_audit',I/'base-policy',I/'restore-sepolicy',I/'restore-sepolicy'],expect=None,timeout=10);assert qf.returncode!=0 and 'data_av==1' in qf.stderr
run(['python3','-B',R/'scripts/independent_structure.py'],timeout=30)
runpy.run_path(str(R/'scripts/query_matrix.py'))
run(['python3','-B',R/'tests/policy_checks.py'],timeout=190)
runpy.run_path(str(R/'scripts/negative_fixtures.py'))
patch=R/'tmp/patch-application';shutil.copytree(R/'baseline',patch)
for name in ['three-file-policy-correction.patch','offline-xperm-test-support.patch']:run(['/usr/bin/patch','-p1','-i',R/'patches'/name],cwd=patch)
for name in ['source/policy_build.c','source/policy_audit.c','tests/policy_checks.py','tests/policy_xperms.c']:assert (patch/name).read_bytes()==(R/name).read_bytes()
(R/'evidence/reproduction.json').write_text(json.dumps(dict(outputs=outputs,actual_candidate_audit=json.loads(q.stdout),frozen_rejected=dict(returncode=qf.returncode,stderr=qf.stderr),patches_reproduce_delivered_sources=True),indent=2)+'\n')
print('REPRODUCTION_PASS')
