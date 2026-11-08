from bounded import R,run
import hashlib,json
T=R/'tools/host';I=R/'inputs';out=R/'artifacts/review-adversarial';out.mkdir()
run(['/usr/bin/clang','-O2','-Wall','-Wextra','-I'+str(T/'libsepol/include'),R/'tests/review_mutate.c',T/'libsepol/src/libsepol.a','-o',T/'review_mutate'])
modes=['data-missing-read','data-wrong-driver','data-duplicate-singleton','old-duplicate-singleton','old-extra-datum','helper-missing-boot-av','helper-missing-system-xperm','helper-duplicate-target','helper-boot-write','helper-sysadmin','helper-extra-fd','changed-transition','data-auditallow','changed-policycap','changed-role','changed-initial-context','add-conditional']
rows=[]
for mode in modes:
 p=out/(mode+'.policy');run([T/'review_mutate',I/'reviewed-policy',p,mode],timeout=10)
 load=run([T/'policy_query',p,'u:r:os_rescue:s0','u:object_r:rescue_userdata_device:s0','blk_file'],timeout=10)
 audit=run([T/'policy_audit',I/'base-policy',p,I/'restore-sepolicy'],expect=None,timeout=10)
 assert audit.returncode!=0 and 'Assertion failed' in audit.stderr,(mode,audit)
 behavior=None
 if mode in ['helper-boot-write','helper-sysadmin','helper-extra-fd']:
  tgt,cls,permission={'helper-boot-write':('u:object_r:rescue_boot_device:s0','blk_file','write'),'helper-sysadmin':('u:r:p10_restore:s0','capability','sys_admin'),'helper-extra-fd':('u:r:adbd:s0','fd','use')}[mode]
  behavior=run([T/'policy_constraints',p,'u:r:p10_restore:s0',tgt,cls,permission],timeout=10).stdout
 if mode=='data-missing-read':behavior=run([T/'policy_constraints',p,'u:r:os_rescue:s0','u:object_r:rescue_userdata_device:s0','blk_file','read'],expect=1,timeout=10).stdout
 if mode=='data-wrong-driver':
  behavior=json.loads(run([T/'policy_xperms',p,'os_rescue','rescue_userdata_device','0x1372'],timeout=10).stdout);assert behavior['allowed']==[0x1372]
 if mode=='old-extra-datum':
  behavior=json.loads(run([T/'policy_xperms',p,'os_rescue','rescue_boot_device','0x1372'],timeout=10).stdout);assert behavior['allowed']==[0x1272,0x1372]
 if mode=='changed-transition':behavior=run([T/'policy_query',p,'u:r:os_rescue:s0','u:object_r:p10_restore_exec:s0','process','--transition'],timeout=10).stdout;assert behavior.strip()=='u:r:os_rescue:s0'
 if mode=='add-conditional':
  q=run([T/'policy_xperms',p,'os_rescue','rescue_userdata_device','0x1272'],expect=None,timeout=10);assert q.returncode!=0 and '!p.cond_list' in q.stderr;behavior=q.stderr
 rows.append(dict(mode=mode,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,full_binary_libsepol_load=True,audit_returncode=audit.returncode,audit_stderr=audit.stderr,behavior=behavior))
# Demonstrate the intended caller trust boundary: the fourth argument must be externally pinned.
ref=out/'UNTRUSTED-altered-reference.policy';run([T/'review_mutate',I/'restore-sepolicy',ref,'helper-extra-fd'],timeout=10)
paired=run([T/'policy_audit',I/'base-policy',out/'helper-extra-fd.policy',ref],timeout=10)
(R/'evidence/review-adversarial.json').write_text(json.dumps(dict(passed=True,count=len(rows),fixtures=rows,trust_boundary=dict(untrusted_matching_reference_accepted=True,stdout=paired.stdout,meaning='Auditor is a relational comparator, not a pin verifier; integration must authenticate all three input identities before audit as already documented')),indent=2)+'\n')
print('REVIEW_ADVERSARIAL_PASS',len(rows))
