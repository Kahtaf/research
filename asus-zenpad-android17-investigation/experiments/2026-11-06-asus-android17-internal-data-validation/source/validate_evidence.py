from pathlib import Path
import sys,json,hashlib,re
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'inputs'))
from analyze_materials import analyze_materials
m=json.loads((R/'evidence/image-manifest.json').read_text());assert m['bytes']==11331268096 and m['sha256']=='1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1'
offset=0
for i,c in enumerate(m['chunks']):
 assert c['offset']==offset and c['size']==min(33554432,m['bytes']-offset) and re.fullmatch('[0-9a-f]{64}',c['sha256']);offset+=c['size']
assert offset==m['bytes'] and len(m['chunks'])==338 and m['independent_reread_sha256']==m['sha256']
f=json.loads((R/'evidence/fresh_userdata.reference-1MiB.json').read_text());assert f['sha256']==m['sha256'] and f['bytes']==m['bytes'] and len(f['chunks'])==10807
payloads=json.loads((R/'inputs/payload-manifest.json').read_text());run=R/'evidence/runtime-r2';total=0
for n in (1,2):
 result=json.loads((run/f'result-{n}.json').read_text());log=(run/f'serial-{n}.log').read_text();checks=analyze_materials(log,payloads)
 assert result['passed'] and result['guest']==dict(phase=n,failures=0) and result['qemu_returncode']==0 and not result['timed_out']
 assert len(checks)==68 and all(c['passed'] for c in checks) and checks==result['material_hashes'];total+=len(checks)
 assert 'CHECK clean_data_umount rc=0' in log and 'CHECK full_partition_bytes rc=0' in log and 'CHECK exact_features rc=0' in log
 assert 'CHECK persistent_user_xattr rc=0' in log and 'CHECK sentinel_attributes rc=0' in log and 'CHECK sentinel_all_bytes rc=0' in log
 assert 'CHECK system_uid_access_and_keystore_denial rc=0' in log and log.count('CHECK init_directory_attributes rc=0')==20
 assert result['sentinel_expected_sha256']+'  /data/system/fullsize-sentinel.bin' in log
 assert (run/f'e2fsck-{n}.txt').read_text().endswith('exit=0\n')
 cmd=json.loads((run/f'qemu-{n}.json').read_text());assert cmd[cmd.index('-smp')+1]=='2' and cmd[cmd.index('-m')+1]=='1536' and cmd[cmd.index('-nic')+1]=='none'
 assert '/r2/data-qa.raw,' in cmd[cmd.index('-drive')+1] and 'pristine' not in ' '.join(cmd)
summary=json.loads((run/'result.json').read_text());assert summary['passed'] and summary['pristine_after_sha256']==m['sha256']
negative=json.loads((R/'evidence/negative-tests.json').read_text());assert negative['passed'] and len(negative['cases'])==18 and all(x['rejected'] for x in negative['cases'])
assert json.loads((R/'evidence/pristine-allocations.json').read_text())['passed']
assert json.loads((R/'evidence/android-init-pins.json').read_text())['captured_init_matches_committed_source']
assert (R/'source/guest_init.c').read_bytes()==(run/'guest_init.c').read_bytes()
out=dict(passed=True,guest_boots=2,material_hashes=total,negative_cases=18,primary_manifest_chunks=338,reference_transport_chunks=10807,pristine_sha256=m['sha256'])
(R/'evidence/local-validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
