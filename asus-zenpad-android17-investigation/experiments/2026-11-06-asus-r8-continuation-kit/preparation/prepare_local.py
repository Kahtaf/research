from pathlib import Path
import json,hashlib,difflib,shutil
R=Path(__file__).resolve().parents[1];OLD=R.parent/'2026-11-06-asus-r7-continuation-kit'
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['integrate.py','build.sh','verify_product_r3.py','validate_completed_product.py']:
 p=R/'scripts'/n;s=(OLD/'scripts'/n).read_text().replace('r7','r8')
 if n=='integrate.py':
  s=s.replace("read(plan['prior_staged_receipt'])['product_after'], 'Already-integrated r3 device preimage mismatch'","read(plan['r7_staged_receipt'])['product_after'], 'Already-integrated r7 device preimage mismatch'")
  s=s.replace("| inputs | sensors, 'Product change selection mismatch'","| inputs | sensors | {'sepolicy/vendor/file_contexts'}, 'Product change selection mismatch'")
  s=s.replace("('BoardConfig.mk', 'device.mk', 'rootdir/ueventd.rc')","('BoardConfig.mk', 'device.mk', 'rootdir/ueventd.rc', 'connectivity/src/driver_cmd_p00a.c', 'sepolicy/vendor/file_contexts')")
 if n=='build.sh':
  s=s.replace('m -j8 ','run_m ')
  s=s.replace('# Never repeat cleaning.', '''# Each m call rotates Soong logs. Freeze the authentic native evidence before
# another invocation, including on failure; never replay commands from this log.
run_m() {
    local phase_rc=0
    m showcommands -j8 "$@" || phase_rc=$?
    python3 -B "$kit/scripts/capture_build_evidence.py" "$kit" "$1" "$phase_rc"
    return "$phase_rc"
}
# Never repeat cleaning.''')
 if n=='validate_completed_product.py':
  s=s.replace("'sensor_delta_sha256': sha(plan['sensor_delta']),", "'r8_delta_sha256': sha(plan['r8_delta']), 'sensor_delta_sha256': sha(plan['sensor_delta']),")
  s=s.replace("properties = []", "from verify_zram_context import verify as verify_zram\n    write(o / 'zram-context.json', verify_zram(partition, policy, b / 'sefcontext_compile', o / 'zram-context'))\n    properties = []")
 p.write_text(s)
p=R/'inputs/plan.json';plan=json.loads((OLD/'inputs/plan.json').read_text());plan=json.loads(json.dumps(plan).replace('/asus-reviewed-build-kit/r7/','/asus-reviewed-build-kit/r8/').replace('/asus-product-integration-staging/r7','/asus-product-integration-staging/r8').replace('/asus-reviewed-build-kit/r7"','/asus-reviewed-build-kit/r8"'))
plan.update(revision='r8',prior_revision='r7',original_pids=plan['original_pids']+[1560115,1560446],parent_contract='PLAN_ONLY default; exact terminal r7 parent acceptance required; only reviewed WPA source boundary and exact zram0 context; authentic native command evidence; no physical GO')
root=plan['run_root'];prior='/srv/android/asus-reviewed-build-kit/r7'
plan.update(r7_kit=prior,r7_plan=prior+'/inputs/plan.json',r7_integration=root+'/inputs/r7-integration.json',r7_staged_receipt=root+'/inputs/r7-STAGED.json',r7_staging_manifest=root+'/inputs/r7-staging-manifest.json',r7_preservation=root+'/inputs/r7-preservation.json',r8_delta=root+'/inputs/r8-delta.json',staging_manifest=root+'/inputs/r8-staging-manifest.json')
for path,digest in json.loads((R/'evidence/remote-inputs.json').read_text())['files_sha256'].items():
 if not path.startswith('device/'):plan['external_pins']['/srv/android/lineage24/'+path]=digest
write(p,plan)
shutil.copyfile(OLD/'inputs/STAGED.json',R/'inputs/r7-STAGED.json')
write(R/'inputs/r7-integration.json',json.loads((R/'evidence/remote-inputs.json').read_text())['r7_integration'])
# Two exact future source postimages, with local preimages and compact diffs.
import sys
sys.path.insert(0,str(R/'scripts'))
from continuation import WPA,CONTEXT,INCLUDES,BOUNDARY,ZRAM
rows={}
for rel in [WPA,CONTEXT]:
 b=(R/'inputs/public-source/device/asus/p00a'/rel).read_bytes();after=b.replace(INCLUDES,BOUNDARY) if rel==WPA else b+ZRAM
 pre=R/'inputs/r8-preimages'/rel;post=R/'inputs/r8-postimages'/rel
 pre.parent.mkdir(parents=True,exist_ok=True);post.parent.mkdir(parents=True,exist_ok=True);pre.write_bytes(b);post.write_bytes(after)
 rows[rel]=dict(before=sha(pre),after=sha(post))
 (R/'source'/('wpa-include-boundary.patch' if rel==WPA else 'zram-context.patch')).write_text(''.join(difflib.unified_diff(b.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/device/asus/p00a/'+rel,tofile='b/device/asus/p00a/'+rel)))
write(R/'inputs/r8-delta.json',rows)
write(R/'inputs/r7-STAGED.json',json.loads((OLD/'inputs/STAGED.json').read_text()))
s=json.loads((OLD/'inputs/STAGED.json').read_text())
for rel,row in rows.items():s['product_after'][rel]={'sha256':row['after']}
write(R/'inputs/STAGED.json',s)
print(json.dumps(rows,indent=2))
