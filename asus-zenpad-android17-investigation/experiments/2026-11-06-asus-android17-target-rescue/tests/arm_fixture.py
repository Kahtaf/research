"""Offline assembler test only: synthetic SYSTEM/CID, actual saved BOOT, and
read-only pristine validated p26 input. This is NOT a parent-approved device manifest."""
from pathlib import Path
import hashlib,json,sys,os
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
from manifest import build
from client import parse
out=R/'artifacts/TEST-ONLY-arming';out.mkdir()
data=Path('/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw')
before=data.stat()
boot=R/'inputs/initial/boot.bin';assert boot.read_bytes()==(R/'inputs/verify/boot.bin').read_bytes()
system=R/'artifacts/fullsize-r3/reviewed-system.raw'
review={'cid_sha256':hashlib.sha256(b'0'*32).hexdigest(),'primary_gpt_sha256':'f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae','backup_gpt_sha256':'2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784','images':{
 'original_system':{'path':str(system),'sha256':'61f807473801bf4eb0ba57b079d8480047d8e76412e8c3bddb1a2ea0597d5f4a'},
 'original_boot':{'path':str(boot),'sha256':'7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'},
 'install_system':{'path':str(system),'sha256':'61f807473801bf4eb0ba57b079d8480047d8e76412e8c3bddb1a2ea0597d5f4a'},
 'install_boot':{'path':str(boot),'sha256':'7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'},
 'provision_userdata':{'path':str(data),'sha256':'1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1'}},
 'approvals':{k:True for k in ['durable_original_system_backup','durable_original_boot_backup','durable_original_recovery_backup','independent_rescue_review','clean_internal_data','factory_wifi_bt_preserved_locally','p26_provision_reviewed']}}
(out/'TEST-ONLY-review.json').write_text(json.dumps(review,indent=2)+'\n')
b,rows=build(review);(out/'TEST-ONLY.manifest').write_bytes(b)
parsed=parse(b);refpath=Path('/srv/android/asus-internal-data-validation/evidence/fresh_userdata.reference-1MiB.json');ref=json.loads(refpath.read_text())
assert parsed[4]['size']==ref['bytes'] and parsed[4]['full'].hex()==ref['sha256']
assert [parsed[4]['chunks'][i:i+32].hex() for i in range(0,len(parsed[4]['chunks']),32)]==ref['chunks']
after=data.stat();fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mode,s.st_nlink,s.st_mtime_ns,s.st_ctime_ns)
assert fields(before)==fields(after)
result=dict(passed=True,TEST_ONLY_NOT_DEVICE_APPROVAL=True,manifest_sha256=hashlib.sha256(b).hexdigest(),manifest_bytes=len(b),images=rows,pristine_unchanged=True,pristine_mode=oct(after.st_mode&0o777),pristine_nlink=after.st_nlink,reference_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest(),reference_1MiB_matches=10807)
(R/'evidence/arming-fixture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
