from pathlib import Path
import sys,json,gzip,hashlib
R=Path(__file__).resolve().parents[1];A=R/'artifacts';S=R/'source';sys.path.insert(0,str(S));import bootformat as b
sha=lambda x:hashlib.sha256(x).digest()
def const(n,x):return 'static const unsigned char '+n+'[32]={'+','.join('0x'+x.hex()[i:i+2] for i in range(0,64,2))+'};\n'
e={n:(0o40755,0,0,b'') for n in ['dev','proc','sys','tmp','sbin','system','system/bin','data']}
meta=json.loads((A/'core-input-metadata.json').read_text())
for p in (A/'core-inputs').rglob('*'):
 if p.is_file():n=str(p.relative_to(A/'core-inputs'));e[n]=(*meta[n],p.read_bytes())
e['sbin/ueventd']=(0o120777,0,0,b'../init')
for name,src,mode in [('sbin/os-rescue','os-rescue',0o100700),('sbin/rescue-proxy','rescue-proxy',0o100755),('system/bin/sh','rescue-proxy',0o100755),('sepolicy','restore-sepolicy',0o100644),('file_contexts.bin','file_contexts.bin',0o100644),('rescue.manifest','original-stock.manifest',0o100444)]:
 e[name]=(mode,0,0,(A/src).read_bytes())
assert len(e['rescue.manifest'][3])==115288 and e['rescue.manifest'][3][12:16]==b'\x02\0\0\0'
assert sha(e['rescue.manifest'][3]).hex()=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
cpio=b.make_cpio(e);assert b.parse_cpio(cpio)==e
gz=bytearray(gzip.compress(cpio,compresslevel=9,mtime=0));gz[9]=255
gz.extend(bytes((-len(gz))%4))  # raw newc member requires stream offset aligned to 4
(A/'core.cpio.gz').write_bytes(gz)
h=bytearray((A/'base-header').read_bytes());h[16:20]=bytes(4);h[576:608]=bytes(32)
w=bytearray((A/'base-wrapper').read_bytes());w[4:8]=bytes(4)
k=(A/'base-kernel').read_bytes()
binding='#define CORE_KERNEL_BYTES '+str(len(k))+'U\n#define CORE_GZIP_BYTES '+str(len(gz))+'U\n'
for n,x in [('core_header_sha',h),('core_wrapper_sha',w),('core_kernel_sha',k),('core_gzip_sha',gz)]:binding+=const(n,sha(x))
(S/'core_binding.h').write_text(binding)
(A/'core-entries.json').write_text(json.dumps({n:dict(mode=m,uid=u,gid=g,bytes=len(x),sha256=sha(x).hex()) for n,(m,u,g,x) in e.items()},indent=2)+'\n')
