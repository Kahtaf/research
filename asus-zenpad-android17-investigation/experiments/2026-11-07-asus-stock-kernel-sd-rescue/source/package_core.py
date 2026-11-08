"""Exact original stock 3.18 wrapped kernel and header; no DT/bootarg mutation."""
import gzip,struct
import bootformat as b
KERNEL_SHA='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
def package(entries,wrapped_kernel,header,kw,rw):
 if len(wrapped_kernel)!=7472341 or b.sha(wrapped_kernel)!=KERNEL_SHA:raise ValueError('exact original wrapped stock kernel required')
 if header[:8]!=b'ANDROID!' or len(header)!=2048:raise ValueError('original Android header required')
 if wrapped_kernel[:512]!=kw or wrapped_kernel[:4]!=bytes.fromhex('88168858') or struct.unpack_from('<I',kw,4)[0]!=len(wrapped_kernel)-512:raise ValueError('actual original MTK KERNEL wrapper required')
 if rw[:4]!=kw[:4] or rw[8:40].split(b'\0')[0]!=b'RECOVERY':raise ValueError('actual original MTK RECOVERY wrapper required')
 cp=b.make_cpio(entries);assert b.parse_cpio(cp)==entries
 gz=bytearray(gzip.compress(cp,compresslevel=9,mtime=0));gz[9]=255;gz=bytes(gz);gz+=bytes((-len(gz))%4)
 # Same runtime container proof format: normalized header/wrapper, kernel, core gzip.
 normalized=bytearray(header);struct.pack_into('<I',normalized,8,len(wrapped_kernel));normalized[16:20]=bytes(4);normalized[576:608]=bytes(32)
 wrapper=bytearray(rw);wrapper[4:8]=bytes(4)
 binding=b'ASUSC001'+struct.pack('<II',len(wrapped_kernel),len(gz))+b''.join(bytes.fromhex(b.sha(x)) for x in [normalized,wrapper,wrapped_kernel,gz])
 assert len(binding)==144
 capsule=b.make_cpio({'rescue.current.binding':(0o100444,0,0,binding)})
 ram=b.wrap(rw,gz+capsule);im=b.make_image(header,wrapped_kernel,ram)
 h,k,r,tail=b.parse_image(im)
 assert not tail and k==wrapped_kernel and r==ram
 assert h[:8]==header[:8] and h[12:16]==header[12:16] and h[20:576]==header[20:576] and h[608:]==header[608:]
 assert r[:4]==rw[:4] and r[8:512]==rw[8:512]
 # ungzip returns alignment padding and the exact canonical binding capsule.
 raw,rest=b.ungzip(r[512:]);assert raw==cp and rest.endswith(capsule) and not any(rest[:-len(capsule)])
 return im,gz+capsule,dict(binding_sha256=b.sha(binding),binding_bytes=144,core_gzip_bytes=len(gz),capsule_bytes=len(capsule),wrapped_kernel_sha256=b.sha(k),wrapped_kernel_bytes=len(k),wrapped_kernel_exact=True,stock_header_unchanged_except_sizes_and_id=True,header_cmdline=header[64:576].split(b'\0')[0].decode(),stock_ramdisk_wrapper_preserved_except_size=True,dt_mutated=False,physical_boot_verified=False)
