"""Read feature support from the selected kernel, not the host filesystem tools."""
import hashlib,re,struct
from pathlib import Path
KERNEL_HEADER=Path('/srv/android/asus-android17/kernel-bpf-fd/fs/ext4/ext4.h')
def inspect(header):
 assert header[1080:1082]==b'\x53\xef'
 source=KERNEL_HEADER.read_text().replace('\\\n',' ')
 def mask(kind):
  expression=re.search(r'^#define\s+EXT4_FEATURE_'+kind+r'_SUPP\s+(.+)$',source,re.M).group(1)
  result=0
  for name in re.findall(r'EXT4_FEATURE_'+kind+r'_[A-Z0-9_]+',expression):
   result|=int(re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)',source,re.M).group(1),16)
  return result
 masks={kind:mask(kind) for kind in ['INCOMPAT','RO_COMPAT']}
 values=struct.unpack_from('<III',header,1024+92)
 assert not values[1]&~masks['INCOMPAT'],('Unsupported ext4 incompat',values,masks)
 assert not values[2]&~masks['RO_COMPAT'],('Unsupported ext4 ro_compat',values,masks)
 return dict(features=dict(compat=values[0],incompat=values[1],ro_compat=values[2]),kernel_supported_masks=masks,kernel_header_sha256=hashlib.sha256(KERNEL_HEADER.read_bytes()).hexdigest())
