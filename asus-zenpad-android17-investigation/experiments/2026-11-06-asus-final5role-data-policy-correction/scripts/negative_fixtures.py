import hashlib,json
from bounded import R,run
T=R/'tools/host';I=R/'inputs';A=R/'artifacts';out=A/'negative-fixtures';out.mkdir()
modes=['helper-data-read','helper-data-write','helper-system-write','daemon-p10-write','daemon-disk-write','daemon-generic-write','extra-data-permission','alter-old-av','missing-data-av','missing-data-xperm','data-driver-wide','data-extra-function','alter-old-xperm','helper-extra-function','changed-attribute','changed-bound','changed-permissive','changed-constraint','helper-extra-fd']
rows=[]
for mode in modes:
    p=out/('REJECTED-'+mode+'.policy')
    run([T/'mutate_policy',A/'UNQUALIFIED-future5role-policy',p,mode],timeout=10)
    # Every mutation must still load as a complete binary policy.
    run([T/'policy_query',p,'u:r:os_rescue:s0','u:object_r:rescue_userdata_device:s0','blk_file'],timeout=10)
    behavior=None
    if mode in ['helper-data-read','helper-data-write','helper-system-write','daemon-p10-write','daemon-disk-write','daemon-generic-write']:
        src,tgt,perm={'helper-data-read':('p10_restore','rescue_userdata_device','read'),'helper-data-write':('p10_restore','rescue_userdata_device','write'),'helper-system-write':('p10_restore','rescue_system_device','write'),'daemon-p10-write':('os_rescue','rescue_recovery_device','write'),'daemon-disk-write':('os_rescue','rescue_disk_device','write'),'daemon-generic-write':('os_rescue','block_device','write')}[mode]
        behavior=run([T/'policy_constraints',p,'u:r:'+src+':s0','u:object_r:'+tgt+':s0','blk_file',perm],timeout=10).stdout
    elif mode in ['data-driver-wide','data-extra-function','alter-old-xperm','helper-extra-function']:
        src='p10_restore' if mode=='helper-extra-function' else 'os_rescue';tgt='rescue_boot_device' if mode in ['alter-old-xperm','helper-extra-function'] else 'rescue_userdata_device'
        behavior=json.loads(run([T/'policy_xperms',p,src,tgt,'0x1273'],timeout=10).stdout)
        assert behavior['requested_allowed']
    q=run([T/'policy_audit',I/'base-policy',p,I/'restore-sepolicy'],expect=None,timeout=10)
    assert q.returncode!=0 and 'Assertion failed' in q.stderr,(mode,q)
    rows.append(dict(mode=mode,policy_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),binary_load_passed=True,undesired_effective_behavior=behavior,audit_returncode=q.returncode,audit_stderr=q.stderr,passed=True))
(R/'evidence/negative-fixtures.json').write_text(json.dumps(dict(passed=True,count=len(rows),all_binary_policies_load=True,all_rejected=True,fixtures=rows),indent=2)+'\n')
print('NEGATIVE_FIXTURES_PASS',len(rows))
