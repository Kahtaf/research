from pathlib import Path
import os,json,hashlib,stat,datetime
R=Path('/srv/android/asus-r9-actual-early-runtime-20261106');E=R/'evidence';I=R/'inputs';pins=json.loads((E/'input-pins.json').read_text());checks={}
for n,row in pins['pins'].items():
 p=Path(row['path']);checks[n]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'unchanged':hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']};assert checks[n]['unchanged']
raw=Path(pins['raw']['path']);st=raw.stat();identity=dict(path=str(raw),dev=st.st_dev,inode=st.st_ino,bytes=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=oct(stat.S_IMODE(st.st_mode)));assert identity=={k:v for k,v in pins['raw'].items() if k!='sha256_inherited'}
for n in ['system.qcow2','system-failed-prep-1.qcow2','data.ext4','runtime-initramfs.cpio.gz']:os.chmod(I/n,0o400 if n=='runtime-initramfs.cpio.gz' else 0o444)
serial=(R/'run-runtime-1/serial.log').read_bytes();seal=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pins_reverified=checks,raw_identity=identity,raw_identity_unchanged=True,raw_full_sha256_inherited=pins['raw']['sha256_inherited'],no_additional_fullraw_hash=True,cow_sha256=hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest(),cow_bytes=(I/'system.qcow2').stat().st_size,cow_mode=oct(stat.S_IMODE((I/'system.qcow2').stat().st_mode)),serial_sha256=hashlib.sha256(serial).hexdigest(),serial_bytes=len(serial),runtime_status=json.loads((R/'run-runtime-1/status.json').read_text()),owned_allocated_bytes=sum(p.lstat().st_blocks*512 for p in R.rglob('*') if p.is_file()),owned_logical_bytes=sum(p.lstat().st_size for p in R.rglob('*') if p.is_file()),runtime_fixture_corrections_used=3,runtime_attempts=1,offline_patch_attempts=2,seed_values_and_hashes_exported=False)
assert seal['owned_allocated_bytes']<2*1024**3 and seal['owned_logical_bytes']<2*1024**3
(E/'seal.json').write_text(json.dumps(seal,indent=2));print(json.dumps(seal,indent=2))
