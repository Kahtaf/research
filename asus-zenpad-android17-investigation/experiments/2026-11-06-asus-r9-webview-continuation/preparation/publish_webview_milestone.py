from pathlib import Path
import remote,json,base64
R=Path(__file__).resolve().parents[1]
origin=base64.b64encode((R/'inputs/webview-origin.json').read_bytes()).decode()
s='ORIGIN='+repr(origin)+'\n'+r'''
from pathlib import Path
import os,json,base64,hashlib,datetime,sys
R=Path('/srv/android/asus-reviewed-build-kit/r9');M=Path('/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1');P=Path('/srv/android/asus-product-integration-staging/r9/webview.apk')
sys.path.insert(0,str(R/'scripts'))
from artifact import admit,check_preimage,REL,COMMIT,ORIGIN as REPO
admit(P);check_preimage(Path('/srv/android/lineage24')/REL)
assert not (R/'inputs/kit-pins.json').exists() and not (R/'attempt').exists()
M.mkdir();(M/'receipts').mkdir()
for name in ['artifact-check.json','lineage-lfs-batch.json','selected-lfs-product-audit.json','final-source-audit.json']:
 with (R/'evidence'/name).open('rb') as inp,(M/'receipts'/name).open('xb') as out:out.write(inp.read());out.flush();os.fsync(out.fileno())
with (M/'receipts/source-origin.json').open('xb') as f:f.write(base64.b64decode(ORIGIN));f.flush();os.fsync(f.fileno())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
audit=json.loads((M/'receipts/selected-lfs-product-audit.json').read_text());assert audit['additional_needed_materializations']==[]
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='FROZEN_QUALIFIED_WEBVIEW_INPUT_ONLY',milestone=str(M),artifact=dict(path=str(P),sha256=sha(P),bytes=P.stat().st_size,vm_only=True),source=dict(repository=REPO,commit=COMMIT,lfs_endpoint='https://review.lineageos.org/LineageOS/android_external_chromium-webview_prebuilt_arm64.git/info/lfs',source_pointer_sha256='a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7'),qualification=dict(real_manifest_check_exit=0,all_zip_crc_passed=True,zip_entries=646,original_pointer_failure_retained=True,one_cpu=True,address_space_bytes=1073741824),other_selected_lfs_inputs=dict(additional_needed_materializations=[],scope=audit['scope'],selected_closure_count=audit['selected_closure_count'],selected_source_apks=len(audit['selected_source_apks']),unselected_webview_abis_not_materialized=['arm','x86','x86_64']),boundary=dict(r9_kit_sealed=False,r9_parent_authorized=False,active_source_materialized=False,r9_native_build_started=False,compiler_cache_lineage_complete=False,full_product_qualified=False,physical_go=False),receipts={p.name:dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted((M/'receipts').iterdir())})
with (M/'MILESTONE.json').open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
pins={str(p.relative_to(M)):sha(p) for p in M.rglob('*') if p.is_file()}
with (M/'pins.json').open('x') as f:json.dump(pins,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
seal=dict(path=str(M),pins_sha256=sha(M/'pins.json'),milestone_sha256=sha(M/'MILESTONE.json'),artifact=receipt['artifact'],boundary=receipt['boundary'])
with (M/'SEAL.json').open('x') as f:json.dump(seal,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
P.chmod(0o444)
for p in M.rglob('*'):
 if p.is_file():p.chmod(0o444)
(M/'receipts').chmod(0o555);M.chmod(0o555)
print(json.dumps(dict(seal=seal,milestone=receipt,pins=pins),indent=2))
'''
d=json.loads(remote.run(s));D=R/'milestone';D.mkdir();(D/'SEAL.json').write_text(json.dumps(d['seal'],indent=2,sort_keys=True)+'\n');(D/'MILESTONE.json').write_text(json.dumps(d['milestone'],indent=2,sort_keys=True)+'\n');(D/'pins.json').write_text(json.dumps(d['pins'],indent=2,sort_keys=True)+'\n');print(json.dumps(d['seal'],indent=2))
