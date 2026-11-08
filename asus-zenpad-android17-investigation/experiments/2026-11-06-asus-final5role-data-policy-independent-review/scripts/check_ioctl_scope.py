from bounded import R,run
import json
T=R/'tools/host';p=R/'inputs/reviewed-policy'
q=run([T/'policy_xperms',p,'init','block_device','0x1277'],timeout=10)
r=json.loads(q.stdout);assert r['effective_ioctl_av'] and r['matching_xperm_rules']==0 and r['allowed_count']==65536 and r['requested_allowed']
r.pop('allowed');r['meaning']='No whitelist for stock init/generic block pair; daemon/helper singleton claim cannot be globalized.'
(R/'evidence/ioctl-scope-boundary.json').write_text(json.dumps(r,indent=2)+'\n');print('IOCTL_SCOPE_PASS init/generic coarse ioctl has no whitelist')
