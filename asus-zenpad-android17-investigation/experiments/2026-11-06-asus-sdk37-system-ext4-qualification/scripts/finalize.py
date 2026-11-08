from pathlib import Path
import ast, hashlib, json, re, datetime
S=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((S/'evidence'/n).read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
inspection=load('inspection.json');inspection2=load('inspection2.json');prep=load('preparation.json');runtime=load('runtime.json');supp=load('supplement.json')
assert runtime['passed'] and runtime['guest_pass'] and runtime['qemu_exit']==runtime['e2fsck_after_exit']==0
assert runtime['images_unchanged'] and runtime['negative_kernel_error']
assert prep['specimen_raw_bytes']==64*1024**2
assert all(r['before']==r['copied']==r['after'] for r in prep['copies']+load('compiler-copy.json'))
assert len(inspection2['ext4_source_parity'])==41 and all(r['equal']for r in inspection2['ext4_source_parity'])
for n,e in [('system-restored.raw',0),('system.sparse',0),('unsupported.raw',1)]:assert supp['header_checks'][n]['exit']==e
assert supp['header_gate_source_sha256']==sha(S/'scripts/check_system_header.py')
headers=[json.loads(supp['header_checks'][n]['output'])for n in ['system-restored.raw','system.sparse']]
assert headers[0]['superblock_sha256']==headers[1]['superblock_sha256']
source=(S/'source/ext4.h').read_text().replace('\\\n','')
defines=dict(re.findall(r'^#define\s+(EXT4_FEATURE_[A-Z0-9_]+)\s+([^\n]+)',source,re.M))
def value(n):
 def walk(t):
  if isinstance(t,ast.Constant) and isinstance(t.value,int):return t.value
  if isinstance(t,ast.Name):return value(t.id)
  if isinstance(t,ast.BinOp) and isinstance(t.op,ast.BitOr):return walk(t.left)|walk(t.right)
  raise ValueError(ast.dump(t))
 return walk(ast.parse(defines[n].split('/*',1)[0].strip(),mode='eval').body)
inc=value('EXT4_FEATURE_INCOMPAT_SUPP');ro=value('EXT4_FEATURE_RO_COMPAT_SUPP')
assert 0x42&~inc==0 and 0x7b&~ro==0 and 0x80000000&inc==0
configs={}
for n in ['virtual','physical']:
 lines=(S/'source'/f'{n}.config').read_text().splitlines();m={}
 for l in lines:
  if l.startswith('CONFIG_') and '='in l:k,v=l.split('=',1);m[k]=v
  elif l.startswith('# CONFIG_')and l.endswith(' is not set'):m[l[2:-11]]='n'
 configs[n]={k:m.get(k,'absent')for k in ['CONFIG_ARM64_4K_PAGES','CONFIG_EXT4_FS','CONFIG_EXT4_FS_SECURITY','CONFIG_EXT4_FS_POSIX_ACL','CONFIG_EXT4_ENCRYPTION','CONFIG_64BIT']}
assert configs['virtual']==configs['physical']
refs={}
for n in ['REPORT.md','acceptance.json','next-fixture-contract.json','evidence/parent-scoped-acceptance.json']:
 p=S.parent/'2026-11-06-asus-memory-firstboot-kernel-qualification'/n;refs[str(p.relative_to(S.parent))]=sha(p)
for n in ['verify_full_images.py','validate_completed_product.py']:
 p=S.parent/'2026-11-06-asus-r8-continuation-kit/scripts'/n;refs[str(p.relative_to(S.parent))]=sha(p)
source_map={r['path']:r['virtual']for r in inspection2['ext4_source_parity']}
proof=dict(ext4_files=len(source_map),selected_source_map_sha256=hashlib.sha256(json.dumps(source_map,sort_keys=True,separators=(',',':')).encode()).hexdigest(),source_map=source_map,kernel_supported_incompat_mask=hex(inc),kernel_supported_rw_ro_compat_mask=hex(ro),kernel_compat_mask_not_used_as_allowlist=True,profile=dict(compat='0x28',incompat='0x42',ro_compat='0x7b'),matching_config_options=configs,references_sha256=refs)
if (S/'evidence/source-support.json').exists():
 assert load('source-support.json')['references_sha256']==refs, 'Pinned parent authority changed'
dump(S/'evidence/source-support.json',proof)
for n,v in runtime['logs'].items():(S/'evidence'/('accepted-'+n)).write_text(v)
for n,v in prep['logs'].items():
 if n not in ['full-size-noaction.log','full-size-noaction-existing.log']:(S/'evidence'/('preparation-'+n)).write_text(v)
result=dict(schema_version=1,utc=json.loads((S/'acceptance.json').read_text())['utc'] if (S/'acceptance.json').exists() else datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='PASS_BOUNDED_SDK37_SYSTEM_EXT4_MECHANISM_ON_PINNED_VIRTUAL_4_9',remote_root=inspection['remote_root'],accepted_runtime=prep['fixture']+'/runtime-r4',kernel_sha256=runtime['kernel_sha256'],config_sha256=runtime['config_sha256'],physical_reference_kernel_sha256='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1',physical_reference_config_sha256='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2',specimen=dict(path=prep['fixture']+'/system-restored.raw',bytes=prep['specimen_raw_bytes'],sha256=prep['specimen_raw_sha256'],feature_masks=proof['profile'],block_bytes=4096,inode_bytes=256),runtime=dict(mount_read_xattr_unmount_passed=True,negative_unknown_incompat_80000000_rejected=True,qemu_exit=0,e2fsck_before_exit=0,e2fsck_after_exit=0,small_images_byte_identical_after=True,limits=runtime['limits']),ext4_source_files_equal_physical=41,packaged_wrapper_available_at_inspection=False,wrapper_mechanism='Captured public BuildImageMkfs and ConstructE2fsCommands functions; copied actual existing SDK37 mke2fs/e2fsdroid binaries',missing_producer=dict(module='python_binary_host mkuserimg_mke2fs',source='system/extras/ext4_utils/Android.bp',output='out/soong/.intermediates/system/extras/ext4_utils/mkuserimg_mke2fs/linux_glibc_x86_64/mkuserimg_mke2fs',installed='out/host/linux-x86/bin/mkuserimg_mke2fs'),full_SYSTEM_read_or_mounted=False,full_SYSTEM_compatible=None,full_SYSTEM_compatibility_status='PENDING_ACTUAL_COMPLETED_IMAGE_GATES',android_runtime_qualified=False,whole_kernel_equivalent=False,physical_GO=False,flash_ready=False,future_gate='FINAL-SYSTEM-GATE.md',source_support=proof['selected_source_map_sha256'])
dump(S/'acceptance.json',result)
print(json.dumps({'decision':result['decision'],'source_support_masks':[hex(inc),hex(ro)],'matching_options':configs['virtual'],'copies_verified':len(prep['copies'])+len(load('compiler-copy.json')),'ext4_files':41},indent=2))
