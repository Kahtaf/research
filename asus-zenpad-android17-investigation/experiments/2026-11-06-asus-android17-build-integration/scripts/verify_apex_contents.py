#!/usr/bin/env python3
"""Inspect actual packaged APEX payloads and run Android's rc parser offline."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from ext4_features import inspect
root=Path('/srv/android/lineage24');out=root/'out/target/product/p00a';host=root/'out/host/linux-x86/bin'
work=Path('/srv/android/asus-build-integration/apex-inspection');work.mkdir(exist_ok=True)
records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for partition in ['system','system/product','system/system_ext','system/vendor']:
 for apex in sorted((out/partition/'apex').glob('*')):
  if apex.suffix not in ['.apex','.capex']:continue
  payload_hash=sha(apex)
  dest=work/(apex.stem+'-'+payload_hash[:12])
  if not dest.exists():
   original=apex
   if apex.suffix=='.capex':
    original=work/(apex.stem+'-'+payload_hash[:12]+'.apex')
    with zipfile.ZipFile(apex) as z, z.open('original_apex') as src,original.open('wb') as dst:
     import shutil;shutil.copyfileobj(src,dst)
   cmd=[str(host/'deapexer'),'--debugfs_path',str(host/'debugfs'),'--fsckerofs_path',str(host/'fsck.erofs'),'extract',str(original),str(dest)+'.extracting']
   p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   if p.returncode:raise RuntimeError(p.stdout)
   Path(str(dest)+'.extracting').rename(dest)
  checks=[]
  for rc in sorted((dest/'etc').rglob('*.rc'))+sorted((dest/'etc').rglob('*.[0-9]*rc')):
   p=subprocess.run([str(host/'host_init_verifier'),str(rc)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   checks.append(dict(path=str(rc.relative_to(dest)),sha256=sha(rc),exit_code=p.returncode,output=p.stdout))
  archive_path=apex if apex.suffix=='.apex' else work/(apex.stem+'-'+payload_hash[:12]+'.apex')
  with zipfile.ZipFile(archive_path) as z,z.open('apex_payload.img') as f:header=f.read(4096)
  filesystem_check=inspect(header) if header[1080:1082]==b'\x53\xef' else {'filesystem':'erofs','checked_by':'verify_full_images.py'}
  row=dict(path=str(apex.relative_to(out)),sha256=payload_hash,rc_checks=checks,filesystem_check=filesystem_check)
  if apex.stem=='com.android.runtime':
   row['linkerconfig_files']=[dict(path=str(f.relative_to(dest)),sha256=sha(f)) for f in dest.rglob('linkerconfig') if f.is_file()]
   expected=out/'apex/com.android.runtime/bin/linkerconfig'
   assert expected.is_file()
   assert any(f['sha256']==sha(expected) for f in row['linkerconfig_files'])
   row['built_linkerconfig_sha256']=sha(expected)
   row['matches_r7_linkerconfig']=sha(expected)=='f697b2f950e3693449989cfc3e1c94ae9845f48dc9ff1e9af271b01a815bd157'
  records.append(row)
Path(sys.argv[1]).write_text(json.dumps(records,indent=2)+'\n')
assert records
assert all(c['exit_code']==0 for r in records for c in r['rc_checks'])
print(len(records),'APEX payloads inspected;',sum(len(r['rc_checks']) for r in records),'APEX rc files passed actual host_init_verifier')
