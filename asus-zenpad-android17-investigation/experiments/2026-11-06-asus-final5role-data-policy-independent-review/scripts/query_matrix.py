import hashlib,json
from bounded import R,run
T=R/'tools/host';I=R/'inputs';A=R/'artifacts'
def rows(q):
    result=[]
    for line in q.stdout.splitlines():
        src,tgt,cls,*allowed=line.split();result.append(dict(source=src,target=tgt,cls=cls,allowed=sorted(allowed)))
    assert len(result)==144
    return result
old=rows(run([T/'policy_reachability',I/'restore-sepolicy'],timeout=10))
new=rows(run([T/'policy_reachability',A/'UNQUALIFIED-future5role-policy'],timeout=10))
review=json.loads((I/'frozen-effective-policy.json').read_text())['rows']
review=[dict(source=r['source'].split(':')[2],target=r['target'].split(':')[2],cls=r['cls'],allowed=r['allowed']) for r in review]
assert old==review
changes=[]
for before,after in zip(old,new):
    assert (before['source'],before['target'],before['cls'])==(after['source'],after['target'],after['cls'])
    if before!=after:changes.append(dict(before=before,after=after))
assert len(changes)==1 and changes[0]==dict(before=dict(source='os_rescue',target='rescue_userdata_device',cls='blk_file',allowed=[]),after=dict(source='os_rescue',target='rescue_userdata_device',cls='blk_file',allowed=sorted(['open','read','write','getattr','ioctl'])))
(R/'evidence/effective-policy.json').write_text(json.dumps(dict(passed=True,rows_per_policy=144,old_rows=old,rows=new,changes=changes,frozen_rows_match_independent_review=True,policy_sha256=hashlib.sha256((A/'UNQUALIFIED-future5role-policy').read_bytes()).hexdigest(),primary_method='Fresh compiled native libsepol compute_av queries, TE/MLS/RBAC; xperms separately queried'),indent=2)+'\n')
print('EFFECTIVE_POLICY_PASS',len(new),'rows, exactly one changed AV row')
