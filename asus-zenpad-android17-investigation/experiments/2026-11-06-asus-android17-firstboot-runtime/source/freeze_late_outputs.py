from pathlib import Path
import json,hashlib,zipfile,subprocess as s
R=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/late-outputs-r1';I.mkdir();items=json.loads((R/'evidence/artifact-discovery-r2.json').read_text())['found'];records=[]
for item in items:
 src=Path(item['path'])
 if not (str(src).endswith('/android_arm64_armv8-a/linkerconfig') or src.name=='com.android.adbd.apex'):continue
 b=src.read_bytes();assert hashlib.sha256(b).hexdigest()==item['sha256'];assert b==src.read_bytes();dst=I/src.name;dst.write_bytes(b);dst.chmod(0o755 if src.name=='linkerconfig' else 0o644);r=dict(source=str(src),path=str(dst),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if src.suffix=='.apex':
  with zipfile.ZipFile(dst) as z:
   r['zip_entries']=z.namelist();r['bundled_public_key_sha256']=hashlib.sha256(z.read('apex_pubkey')).hexdigest();r['manifest_sha256']=hashlib.sha256(z.read('apex_manifest.pb')).hexdigest()
  r['signed_archive_modified']=False;r['runtime_activation_tested']=False
 else:
  cmd=['aarch64-linux-gnu-readelf','-d',str(dst)];p=s.run(cmd,capture_output=True,text=True);r['readelf']=dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0
 records.append(r)
assert len(records)==2;(I/'manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps([dict(path=r['path'],sha256=r['sha256']) for r in records],indent=2))
