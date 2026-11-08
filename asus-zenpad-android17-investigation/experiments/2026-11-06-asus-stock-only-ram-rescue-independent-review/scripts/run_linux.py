from pathlib import Path
import os,resource,subprocess,json,hashlib,shutil
R=Path(__file__).resolve().parents[1]; O=Path('/srv/android/2026-11-06-asus-stock-only-ram-rescue-build')
assert str(R)=='/srv/android/2026-11-06-stock-review'
os.chdir(R);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.environ.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'artifacts'),LC_ALL='C',SOURCE_DATE_EPOCH='1793923200')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p):return {str(f.relative_to(p)):dict(bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(p.rglob('*')) if f.is_file()}
before=inventory(O);(R/'evidence/remote-inputs-before.json').write_text(json.dumps(before,indent=2)+'\n')
for d in ['source','tests']:shutil.copytree(O/d,R/d)
for name in ['assemble_core.py','assemble_final.py','verify_container.py']:shutil.copyfile(O/'scripts'/name,R/'scripts'/name)
names=['base-header','base-kernel','base-wrapper','base-policy','original-stock.manifest','original-recovery.payload','core-input-metadata.json','core.cpio.gz','file_contexts','file_contexts.bin','restore-sepolicy','rescue-proxy','os-rescue','p10-restore','p10-restore-reproduction','legacy-reproduction']
for name in names:shutil.copyfile(O/'artifacts'/name,R/'artifacts'/name)
shutil.copytree(O/'artifacts/core-inputs',R/'artifacts/core-inputs')
shutil.copytree(O/'artifacts/candidate',R/'artifacts/candidate')
assert sha(R/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.p10.raw')=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
assert sha(R/'source/host.py')=='2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9'
logs=[]
def run(cmd,timeout=120):
    p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=timeout)
    logs.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    (R/'evidence/review-run.json').write_text(json.dumps(logs,indent=2)+'\n')
    assert p.returncode==0,(cmd,p.stderr[-2500:],p.stdout[-1500:]);return p.stdout
flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none']
for name,src,extra in [('helper','p10_restore.c',[]),('daemon','rescue.c',['-DP10_HANDOFF']),('legacy','rescue.c',[])]:
    run(['aarch64-linux-gnu-gcc',*flags,*extra,'source/'+src,'-o','artifacts/review-'+name])
    assert (R/'artifacts'/('review-'+name)).read_bytes()==(R/'artifacts'/dict(helper='p10-restore',daemon='os-rescue',legacy='legacy-reproduction')[name]).read_bytes()
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
run(['gcc','-O2','-Wno-discarded-qualifiers','-I'+str(T/'libsepol/include'),'source/policy_build.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_build'])
run(['artifacts/policy_build','artifacts/base-policy','artifacts/review-sepolicy'])
assert (R/'artifacts/review-sepolicy').read_bytes()==(R/'artifacts/restore-sepolicy').read_bytes()
shutil.copyfile(R/'artifacts/file_contexts',R/'artifacts/review-contexts')
run([T/'sefcontext_compile','artifacts/review-contexts'])
assert (R/'artifacts/review-contexts.bin').read_bytes()==(R/'artifacts/file_contexts.bin').read_bytes()
for name in ['core_tests','session_server','test_server','adversarial_core','handoff_server-r2']:
    out='review-handoff-server-r2' if name=='handoff_server-r2' else name
    run(['gcc','-O2','-Wall','-Wno-unused-function','-Wno-misleading-indentation','tests/'+name+'.c','-o','artifacts/'+out])
for name in ['core_tests','adversarial_core']:
    (R/'evidence'/('review-'+name+'.json')).write_text(run(['artifacts/'+name]))
os.environ['RESCUE_TEST_SERVER']=str(R/'artifacts/test_server');os.environ['RESCUE_DAEMON']=str(R/'artifacts/os-rescue')
for name in ['test_adapters.py','host_tests.py','host_durability.py','contract_tests.py','new_manifest_tests.py','handoff_tests-r2.py']:
    run(['python3','-B','tests/'+name])
run(['gcc','-O2','-I'+str(T/'libsepol/include'),'source/policy_audit.c',T/'libsepol/src/libsepol.a','-o','artifacts/policy_audit'])
(R/'evidence/review-policy-structure.json').write_text(run(['artifacts/policy_audit','artifacts/base-policy','artifacts/restore-sepolicy']))
run(['python3','-B','tests/policy_checks.py'])
run(['python3','-B','tests/reproduce.py'])
run(['python3','-B','scripts/verify_container.py'])
run(['python3','-B','scripts/host_edges.py'])
run(['python3','-B','scripts/readonly_reconciliation.py'])
after=inventory(O);assert before==after
(R/'evidence/remote-input-integrity.json').write_text(json.dumps(dict(passed=True,file_count=len(before),all_inputs_unchanged=True,pins=after),indent=2)+'\n')
(R/'evidence/resources.json').write_text(json.dumps(dict(cpu_affinity=sorted(os.sched_getaffinity(0)),address_space=resource.getrlimit(resource.RLIMIT_AS),sequential=True,device_operations=0))+'\n')
print('INDEPENDENT_LINUX_REVIEW_PASS')
