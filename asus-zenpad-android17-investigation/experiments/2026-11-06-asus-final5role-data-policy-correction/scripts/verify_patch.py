import hashlib,json,shutil
from bounded import R,run
out=R/'tmp/patch-application';out.mkdir()
for folder in ['source','tests']:
    shutil.copytree(R/'baseline'/folder,out/folder)
for name in ['three-file-policy-correction.patch','offline-xperm-test-support.patch']:
    run(['/usr/bin/patch','-p1','--dry-run','-i',R/'patches'/name],cwd=out,timeout=10)
    run(['/usr/bin/patch','-p1','-i',R/'patches'/name],cwd=out,timeout=10)
files=['source/policy_build.c','source/policy_audit.c','tests/policy_checks.py','tests/policy_xperms.c']
assert all((out/p).read_bytes()==(R/p).read_bytes() for p in files)
(R/'evidence/patch-application.json').write_text(json.dumps(dict(passed=True,baseline_preimages_used=True,both_patches_apply=True,files_equal_source=True,files=files),indent=2)+'\n')
print('PATCH_APPLICATION_PASS')
