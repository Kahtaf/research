from pathlib import Path
import gzip,zlib,json,hashlib,re,struct
S=Path(__file__).resolve().parents[1];W=S.parent
K=W/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
pins=[]
for rel in ['fs/ext4/ext4.h','fs/ext4/super.c','drivers/misc/mediatek/include/mt-plat/sd_misc.h']:
 b=(K/rel).read_bytes();dest='kernel318__'+rel.replace('/','_');(S/'inputs'/dest).write_bytes(b);pins.append(dict(path=str(K/rel),file=dest,sha256=hashlib.sha256(b).hexdigest()))
# Bounded decompression of the exact saved recovery kernel, not any private partition.
p=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
ks=struct.unpack_from('<I',b,8)[0];kernel=b[2048:2048+ks]
z=zlib.decompressobj(31);raw=z.decompress(kernel[512:],64*1024*1024);assert z.eof and len(raw)<64*1024*1024
start=raw.find(b'IKCFG_ST');end=raw.find(b'IKCFG_ED',start)
cfg=gzip.decompress(raw[start+8:end]) if 0<=start<end else None
if cfg is not None:
 assert len(cfg)<1024*1024
 (S/'inputs/stock-kernel.config').write_bytes(cfg)
version=re.search(rb'Linux version [^\0]+',raw).group(0).decode()
# Interpret published ASUS source feature masks. This is not a binary-identical rebuild assertion.
h=(S/'inputs/kernel318__fs_ext4_ext4.h').read_text().replace('\\\n',' ')
defines=dict(re.findall(r'^#define\s+(EXT[234]_FEATURE_\w+)\s+([^\n]+)',h,re.M))
def value(n):
 v=defines[n].split('/*')[0].strip()
 if re.fullmatch(r'0x[0-9A-Fa-f]+',v):return int(v,16)
 names=re.findall(r'EXT[234]_FEATURE_\w+',v);assert names,(n,v)
 r=0
 for name in names:r|=value(name)
 return r
inc=value('EXT4_FEATURE_INCOMPAT_SUPP');ro=value('EXT4_FEATURE_RO_COMPAT_SUPP')
# Existing A17 image receipt avoids any fullsize raw reads or new image.
p=W/'2026-11-06-asus-android17-internal-data-validation/evidence/pristine-inspection.json';old=json.loads(p.read_text())
(S/'inputs/a17-inspection-receipt.json').write_text(p.read_text())

features=['FILETYPE','EXTENTS'];rof=['SPARSE_SUPER','LARGE_FILE','GDT_CSUM','DIR_NLINK','EXTRA_ISIZE']
need_inc=sum(value('EXT4_FEATURE_INCOMPAT_'+x) for x in features);need_ro=sum(value('EXT4_FEATURE_RO_COMPAT_'+x) for x in rof)
assert int(old['incompat'],16)==need_inc and int(old['ro_compat'],16)==need_ro
assert not need_inc&~inc and not need_ro&~ro
assert (need_inc|0x10000000)&~inc and (need_ro|0x10000000)&~ro
result={'stock_kernel_wrapped_sha256':hashlib.sha256(kernel).hexdigest(),'stock_kernel_version':version,'stock_config_sha256':hashlib.sha256(cfg).hexdigest() if cfg else None,'config_relevant':[x for x in (cfg.decode().splitlines() if cfg else []) if re.search('CONFIG_(EXT4|JBD2|FS_ENCRYPTION|DM_CRYPT|BLK_DEV_DM)',x)],'source_pins':pins,'ASUS318_source_supported_incompat':hex(inc),'ASUS318_source_supported_ro_compat':hex(ro),'A17_features_incompat':hex(need_inc),'A17_features_ro_compat':hex(need_ro),'source_feature_subset_pass':True,'unknown_feature_negative_controls':2,'limits':'Source mask compatibility; stock embedded CONFIG unavailable; not actual 3.18 mount, OEM e2fsck, init, FDE or framework execution.'}
(S/'evidence/filesystem.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
