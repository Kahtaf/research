from pathlib import Path
import os,json,hashlib,stat,datetime
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');E=R/'evidence';S=R/'inputs/native-snapshot';os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});p=json.loads((E/'native-snapshot-pins.json').read_text());verified={}
for name in ['native-snapshot-pins.json','host-sysroot-extra-pins.json','host-gcc-runtime-pins.json','environment-header-pins.json']:
 d=json.loads((E/name).read_text());files=d['files'] if name=='native-snapshot-pins.json' else d
 for rel,row in files.items():
  expected=row['sha256'] if isinstance(row,dict) else row;assert hashlib.sha256((S/rel).read_bytes()).hexdigest()==expected,rel
 verified[name]={'entries':len(files),'passed':True}
for n,row in p['tools'].items():assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'],n
kernel=Path('/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/Image');config=kernel.parent/'config';assert hashlib.sha256(kernel.read_bytes()).hexdigest()=='95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b';assert hashlib.sha256(config.read_bytes()).hexdigest()=='c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834'
admit=json.loads((E/'root-enabled-admission.json').read_text());raw=Path(admit['raw_identity']['path']);st=raw.stat();identity=dict(path=str(raw),dev=st.st_dev,inode=st.st_ino,bytes=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=oct(stat.S_IMODE(st.st_mode)));assert identity==admit['raw_identity'];boot=Path(admit['boot']['path']);assert hashlib.sha256(boot.read_bytes()).hexdigest()=='784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435'
frozen=R/'frozen-namespace-handoff-v1';fp=json.loads((frozen/'pins.json').read_text())
for n,row in fp['files'].items():assert hashlib.sha256((frozen/n).read_bytes()).hexdigest()==row['sha256']
assert hashlib.sha256((frozen/'REPORT.md').read_bytes()).hexdigest()=='a5139b9a288cfe13bf9751a6e95a358e479da892e630ff49da9b0c8802dc813c'
runs={};cowpins={}
for n in ['r1','r2','r3']:
 run=R/('run-runtime-'+n);status=json.loads((run/'status.json').read_text());assert status['raw_identity_unchanged'];runs[n]=status;I=R/'inputs'/('runtime-'+n)
 for name in ['system.qcow2','data.ext4']:os.chmod(I/name,0o444)
 os.chmod(I/'runtime-initramfs.cpio.gz',0o400);cowpins[n]={'bytes':(I/'system.qcow2').stat().st_size,'sha256':hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest(),'DATA_bytes':(I/'data.ext4').stat().st_size,'DATA_mode':'0444','DATA_hash_withheld':True,'entropy_value_and_hash_withheld':True}
old=Path('/srv/android/asus-r9-actual-early-runtime-20261106');assert hashlib.sha256((old/'inputs/system.qcow2').read_bytes()).hexdigest()=='a367784813f5b1fa748013c64a2b853f5fa306a31fb807e4fddd39c8da523322';assert hashlib.sha256((old/'run-runtime-1/serial.log').read_bytes()).hexdigest()=='540959fe59a0b579f5ac99476a352b39c0c62de4e2d83ee82145c020c982a113'
# Bind-local scratch reads are public diagnostics only. No keystore database/key file is inspected.
core=(R/'inputs/root-enabled-init.rc').read_text();at=core.index('    start odsign\n');nextcommands=core[at:at+900];assert 'wait_for_prop odsign.key.done 1' in nextcommands
seal=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_identity=identity,raw_sha256_inherited=admit['raw_sha256_parent_admitted'],raw_identity_unchanged=True,no_additional_fullraw_hash=True,closure_verification=verified,compiler_tools_unchanged=True,kernel_and_config_unchanged=True,frozen_handoff_unchanged=True,old_run1_COW_and_serial_unchanged=True,runtime_runs=runs,owned_cow_pins=cowpins,next_original_init_commands=nextcommands,owned_logical_bytes=sum(x.stat().st_size for x in R.rglob('*') if x.is_file() and not x.is_symlink()),owned_allocated_bytes=sum(x.stat().st_blocks*512 for x in R.rglob('*') if x.is_file() and not x.is_symlink()),budget_bytes=(2*1024+256)*1024**2,runtime_iterations=3,further_runtime_iterations_authorized_in_this_unit=False,TMPDIR=str(R/'tmp'))
assert seal['owned_logical_bytes']<seal['budget_bytes'] and seal['owned_allocated_bytes']<seal['budget_bytes'];(E/'final-seal.json').write_text(json.dumps(seal,indent=2));print(json.dumps({k:v for k,v in seal.items() if k not in ['runtime_runs','next_original_init_commands','owned_cow_pins']},indent=2))
