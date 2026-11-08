"""Read delivered public products only. Never assembles a stand-in candidate."""
from pathlib import Path
import ast,gzip,hashlib,json,struct,sys,difflib
R=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'source'))
import bootformat as b
old=R.parent/'2026-11-07-asus-sd-media-flag-core'
baseline=json.loads((R/'evidence/baseline-pins.json').read_text())
for rel,pin in baseline.items():assert b.sha((old/rel).read_bytes())==pin
for p in list((R/'scripts').glob('*.py'))+list((R/'source').glob('*.py')):ast.parse(p.read_text())
products=json.loads((R/'artifacts/ARTIFACTS.json').read_text())
for name,row in products.items():
 data=(R/'artifacts'/name).read_bytes();assert len(data)==row['bytes'] and b.sha(data)==row['sha256']
for name in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore','rescue-sd-check','rescue-sd-check-runner']:
 d=(R/'artifacts'/name).read_bytes();b.elf_static(d);assert struct.unpack_from('<H',d,16)[0]==2
check=(R/'artifacts/rescue-sd-check').read_bytes()
for text in [b'--offline-prearmed',b'--execute',b'required_execute_trigger=',b'OBSERVED_SEQUENCE_COMPLETE']:
 assert text not in check
raw=gzip.decompress((R/'artifacts/common-rootfs.cpio.gz').read_bytes());e=b.parse_cpio(raw)
assert not any(n in e for n in ['rescue.manifest','rescue.sd.arm','system/bin/sh','sbin/adbd'])
for n in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore']:assert e['sbin/'+n][3]==(R/'artifacts'/n).read_bytes()
for n in ['sepolicy','file_contexts.bin']:assert (R/'artifacts'/n).read_bytes()==(old/'artifacts'/n).read_bytes()
init=e['init.rc'][3].split(b'service rescue-sd-offline',1)[0].replace(b'/sbin/p10-restore ',b'')+b'\n'+(R/'source/init.check.action.rc').read_bytes()
assert init.count(b'start rescue-sd-check')==1 and b'start rescue-sd-offline' not in init and b'service rescue-sd-offline' not in init
# Every explicit restorecon target still exists in the eventual CHECK entries.
check_names=set(e)-{'sbin/p10-restore'}|{'rescue.manifest','rescue.sd.arm','rescue.current.binding'}
for line in init.splitlines():
 if line.strip().startswith(b'restorecon '):
  for target in line.split()[1:]:
   assert target.decode().lstrip('/') in check_names or target==b'/dev/rescue-state'
# Conservative gzip bound using real common bytes + maximum admitted manifest,
# runner ELF, and 64 KiB extra metadata. No image, manifest, arm, or hash is invented.
raw_bound=len(raw)+1024**2+(R/'artifacts/rescue-sd-check-runner').stat().st_size+65536
compressed_bound=raw_bound+(raw_bound>>12)+(raw_bound>>14)+(raw_bound>>25)+64
image_bound=2048+b.align(7472341)+b.align(512+b.align(compressed_bound,4)+512)
assert image_bound<b.PARTITION_SIZE
patch=''
for rel in sorted(baseline):
 if not (R/rel).exists():continue
 before=(old/rel).read_text(errors='replace');after=(R/rel).read_text(errors='replace')
 if before!=after:patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='baseline/'+rel,tofile='stock318/'+rel))
(R/'evidence/source.patch').write_text(patch)
receipt=dict(status='PASS',baseline_files_unchanged=True,actual_static_elfs=6,policy_and_contexts_byte_identical=True,common_cpio_roundtrip=True,common_has_no_private_manifest_or_arm=True,check_frontend_has_no_execution_cli_or_trigger_text=True,check_init_no_selector_or_missing_restorecon_target=True,common_uncompressed_bytes=len(raw),conservative_max_manifest_package_bound_bytes=image_bound,p10_partition_bytes=b.PARTITION_SIZE,candidate_assembled=False,private_inputs_accessed=False,physical_boot_verified=False)
(R/'evidence/local-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
