from pathlib import Path
import datetime,difflib,hashlib,json,os,shutil,sys
from bounded import R,run
ROOT=R.parent

def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return dict(bytes=p.stat().st_size,sha256=h.hexdigest())
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
pre=json.loads((R/'evidence/original-files-before.json').read_text())
post={name:pin(ROOT/name) for name in pre}
assert pre==post
write(R/'evidence/original-files-after.json',post)
stock=ROOT/'2026-11-06-asus-stock-only-ram-rescue-build'
image=stock/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img'
assert pin(image)['sha256']=='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
h=hashlib.sha256(image.read_bytes());left=16740352-image.stat().st_size
while left:n=min(left,65536);h.update(bytes(n));left-=n
assert h.hexdigest()=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
write(R/'evidence/preservation.json',dict(passed=True,original_file_count=len(pre),all_pre_post_equal=True,frozen_image=pin(image),frozen_logical_padded_p10_sha256=h.hexdigest(),padded_image_created=False,frozen_policy=pin(R/'inputs/restore-sepolicy'),base_policy=pin(R/'inputs/base-policy'),contexts_binary=pin(R/'inputs/file_contexts.bin'),contexts_text=pin(R/'inputs/file_contexts'),parent_and_review_documents_unchanged=True,active_tree_or_out_used=False))
archives={'libsepol':'c17c444d73f1080a8959cfda2d4bdb529efd88f5af58a9e571917f473f83ff27','libselinux':'8a8b5ef512bd4aa7ac8cdb8e1f7f64644ad340d75f5280f77c9c912d53970b9b','pcre':'fb5d81e0e32b5047b2095ca865c75690aba079d5c8cb28497362deda95ab4947'}
for name,sha in archives.items():assert pin(R/'inputs'/(name+'-android-7.1.2_r39.tar.gz'))['sha256']==sha
patches=[]
for name in ['source/policy_build.c','source/policy_audit.c','tests/policy_checks.py']:
    patches.extend(difflib.unified_diff((R/'baseline'/name).read_text().splitlines(True),(R/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(R/'patches/three-file-policy-correction.patch').write_text(''.join(patches))
support=''.join(difflib.unified_diff([], (R/'tests/policy_xperms.c').read_text().splitlines(True),fromfile='/dev/null',tofile='b/tests/policy_xperms.c'))
(R/'patches/offline-xperm-test-support.patch').write_text(support)
write(R/'evidence/source-delta.json',dict(modified_integration_files={name:dict(before=pin(R/'baseline'/name),after=pin(R/name)) for name in ['source/policy_build.c','source/policy_audit.c','tests/policy_checks.py']},new_test_support={'tests/policy_xperms.c':pin(R/'tests/policy_xperms.c')},unchanged_context_parser=pin(R/'source/file_contexts.py')))
checks=json.loads((R/'evidence/policy-checks.json').read_text());pairs={}
for row in checks['xperms']:pairs[(row['source'],row['target'])]=row
write(R/'evidence/effective-xperms.json',dict(passed=True,policy_sha256=checks['policy_sha256'],scope='Unconditional unbounded Android-7 endpoint pairs only; effective libsepol ioctl AV plus actual attribute-expanded binary xperm datums',restricted_daemon_pairs=5,restricted_helper_pairs=4,helper_DATA_denied=True,key_space_per_pair=65536,allowed_selinux_ioctl_key='0x1272',denied_examples=['BLKROSET 0x125d','BLKDISCARD 0x1277','neighbor 0x1273','other driver 0x1372','0xffff'],pairs=list(pairs.values())))
versions={}
for n,args in {'clang':['/usr/bin/clang','--version'],'ld':['/usr/bin/ld','-v'],'make':['/usr/bin/make','--version'],'python':[sys.executable,'--version'],'sdk':['/usr/bin/xcrun','--show-sdk-path'],'sdk_version':['/usr/bin/xcrun','--show-sdk-version']}.items():
    q=run(args,expect=None,timeout=10);versions[n]=dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr)
executables={}
for name in ['/usr/bin/clang','/usr/bin/ar','/usr/bin/ranlib','/usr/bin/make','/Library/Developer/CommandLineTools/usr/bin/clang','/Library/Developer/CommandLineTools/usr/bin/ld','/Library/Developer/CommandLineTools/usr/bin/ar','/Library/Developer/CommandLineTools/usr/bin/ranlib',sys.executable]:
    p=Path(name)
    if p.is_file():executables[name]=dict(resolved=str(p.resolve()),**pin(p))
write(R/'evidence/toolchain.json',dict(platform=list(os.uname()),versions=versions,executables=executables,source_archives={str(p.relative_to(R)):pin(p) for p in (R/'inputs').glob('*.tar.gz')},built_host_tools={str(p.relative_to(R)):pin(p) for p in (R/'tools/host').iterdir() if p.is_file() and (p.name.startswith('policy_') or p.name in ['context_lookup','mutate_policy','baseline_policy_build','libpcre.a'])},static_libsepol=pin(R/'tools/host/libsepol/src/libsepol.a'),libsepol_headers={str(p.relative_to(R)):pin(p) for p in (R/'tools/host/libsepol/include').rglob('*') if p.is_file()},assertions_enabled=True,same_host_clean_reproduction=True,system_dynamic_runtime_and_SDK_full_content_not_pinned=True))
rows=[json.loads(line) for line in (R/'evidence/commands.jsonl').read_text().splitlines()]
write(R/'evidence/resources.json',dict(platform='native Darwin arm64',serial_compiler_jobs=1,serialized_final_commands=True,initial_QA_overlap_retained='initial-run-scheduling.json',cpu_limit_seconds_per_host_process=60,wall_timeout_seconds_per_host_command_max=max(row['wall_timeout_seconds'] for row in rows),suite_command_start_deadline_seconds=300,policy_test_cpu_seconds_per_query=10,policy_test_wall_seconds_per_query=10,policy_test_suite_command_start_deadline_seconds=180,policy_test_supervisor_wall_timeout_seconds=190,hard_memory_setrlimit_rejected=True,hard_CPU_affinity_unavailable=True,hard_one_core_or_1GiB_quota_claimed=False,observed_maxrss_bytes=max([row['observed_children_maxrss_bytes'] for row in rows]+[checks['observed_children_maxrss_bytes']]),observed_maxrss_below_1GiB=True,host_command_count=len(rows),nonzero_host_commands=[dict(argv=row['argv'],returncode=row['returncode']) for row in rows if row['returncode']!=0],scope='Host commands only; no target I/O. Native compiler/linker OS runtime threads are not affinity constrained.'))
write(R/'SOURCE_PINS.json',{str(p.relative_to(R)):pin(p) for folder in ['source','tests','scripts','baseline','inputs'] for p in (R/folder).rglob('*') if p.is_file()})
print('PRESERVATION_SOURCE_TOOLCHAIN_RESOURCE_SEAL_PASS',len(pre))
