"""Read exact saved images; extract only selected public startup artifacts."""
import os, resource, hashlib, struct, json, zlib, pathlib, re
resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
limits={'cpu_seconds':90,'address_space_bytes':None}
try:
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, resource.getrlimit(resource.RLIMIT_AS)[1]))
    limits['address_space_bytes']=1024**3
except ValueError as exc:
    limits['address_space_error']=str(exc)
    try:
        resource.setrlimit(resource.RLIMIT_DATA, (1024**3, resource.getrlimit(resource.RLIMIT_DATA)[1]))
        limits['data_segment_bytes']=1024**3
    except ValueError as exc:
        limits['data_segment_error']=str(exc)
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k] = '1'
R = pathlib.Path(__file__).resolve().parents[1]
W = R.parent
H = lambda b: hashlib.sha256(b).hexdigest()
align = lambda n,a=2048: (n+a-1)//a*a
sources = {
 'candidate': ('2026-11-06-asus-stock-only-ram-rescue-build/artifacts/candidate/UNAPPROVED-STOCK-ONLY.img','5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'),
 'stock': ('2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin','902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'),
}
def cpio(b, offset=0):
    rows=[]; entries={}; p=offset
    for _ in range(4096):
        assert b[p:p+6] in (b'070701',b'070702'), (p,b[p:p+16])
        f=[int(b[p+6+8*i:p+14+8*i],16) for i in range(13)]
        size,ns=f[6],f[11]; assert ns<4096 and size<32*1024**2
        name=b[p+110:p+110+ns-1].decode(); p=align(p+110+ns,4)
        value=b[p:p+size]; assert len(value)==size; p=align(p+size,4)
        rows.append(dict(name=name,mode=oct(f[1]),uid=f[2],gid=f[3],nlink=f[4],bytes=size,sha256=H(value)))
        if name=='TRAILER!!!': return rows,entries,p
        assert name not in entries
        entries[name]=(f,value)
    raise AssertionError('cpio bounded')
def fdt(b,base):
    magic,total,so,st,ro,ver,last,cpuid,stringsz,structsz=struct.unpack_from('>10I',b,base)
    assert magic==0xd00dfeed and 40<=total<=len(b)-base
    strings=b[base+st:base+st+stringsz]; p=base+so; stack=[]; props=[]
    while p<base+so+structsz:
        token=struct.unpack_from('>I',b,p)[0];p+=4
        if token==1:
            end=b.index(b'\0',p);stack.append(b[p:end].decode());p=base+align(end+1-base,4)
        elif token==2:stack.pop()
        elif token==3:
            n,off=struct.unpack_from('>II',b,p);p+=8;v=b[p:p+n];p=base+align(p+n-base,4)
            end=strings.index(b'\0',off);name=strings[off:end].decode();path='/'.join(stack)
            if any(s in path.lower() for s in ('chosen','reserved','memory')) or name in ('model','compatible','#address-cells','#size-cells'):
                props.append(dict(path=path,name=name,hex=v.hex(),text=v.rstrip(b'\0').decode('ascii','replace') if all(c==0 or 32<=c<127 for c in v) else None))
        elif token==9:break
        elif token!=4:raise AssertionError(token)
    reservations=[]; p=base+ro
    for _ in range(128):
        a,n=struct.unpack_from('>QQ',b,p);p+=16
        if a==0 and n==0:break
        reservations.append(dict(address=hex(a),bytes=n,end=hex(a+n)))
    return dict(offset=base,bytes=total,sha256=H(b[base:base+total]),version=ver,reservations=reservations,properties=props)
report={}; kernels={}; configs={}
for label,(rel,pin) in sources.items():
    src=W/rel; b=src.read_bytes(); assert H(b)==pin
    assert b[:8]==b'ANDROID!'
    fields=struct.unpack_from('<10I',b,8);ks,ka,rs,ra,ss,sa,ta,page,dts,unused=fields
    assert page==2048 and ss==0
    k=b[page:page+ks];ro=page+align(ks,page);ram=b[ro:ro+rs]
    assert k[:4]==ram[:4]==bytes.fromhex('88168858')
    assert struct.unpack_from('<I',k,4)[0]==len(k)-512
    assert struct.unpack_from('<I',ram,4)[0]==len(ram)-512
    ident=hashlib.sha1(k+struct.pack('<I',ks)+ram+struct.pack('<II',rs,0)).digest()+bytes(12)
    assert b[576:608]==ident
    streams=[]; allentries={}; rest=ram[512:];offset=0
    while rest:
        zeros=len(rest)-len(rest.lstrip(b'\0'));offset+=zeros;rest=rest[zeros:]
        if not rest:break
        if rest[:2]==b'\x1f\x8b':
            d=zlib.decompressobj(31);raw=d.decompress(rest,32*1024**2);assert d.eof and not d.unconsumed_tail
            used=len(rest)-len(d.unused_data);rows,entries,end=cpio(raw)
            assert not any(raw[end:]);kind='gzip-newc';expanded=len(raw)
        else:
            rows,entries,used=cpio(rest);kind='raw-newc';expanded=used
        streams.append(dict(offset=offset,absolute_image_offset=ro+512+offset,kind=kind,bytes=used,expanded_bytes=expanded,entries=rows))
        for n,v in entries.items():
            assert n not in allentries, ('duplicate',n)
            allentries[n]=v
        offset+=used;rest=rest[used:]
    dest=R/'extracted'/label;dest.mkdir(parents=True,exist_ok=True)
    wanted={'init','sbin/adbd','sbin/rescue-proxy','sbin/os-rescue','init.rc','default.prop','sepolicy','file_contexts','file_contexts.bin','property_contexts','seapp_contexts','service_contexts','ueventd.rc'}
    for n,(f,v) in allentries.items():
        if n in wanted or n.startswith('init.') and n.endswith('.rc') or n.startswith('ueventd.') and n.endswith('.rc'):
            p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
    kernels[label]=k
    kd=zlib.decompressobj(31); image=kd.decompress(k[512:],64*1024**2)
    assert kd.eof and not kd.unconsumed_tail
    # Public kernel decompression stays in memory. The compressed kernel can carry appended DTBs.
    kernel_gzip=dict(compressed_bytes=len(k)-512-len(kd.unused_data),expanded_bytes=len(image),expanded_sha256=H(image),appended_bytes=len(kd.unused_data),arm64_header=image[:64].hex())
    dtbs=[]
    for origin,blob in [('wrapped-compressed-kernel',k),('decompressed-kernel',image)]:
      for m in re.finditer(re.escape(bytes.fromhex('d00dfeed')),blob):
        try:
            dt=fdt(blob,m.start());dt['origin']=origin;dtbs.append(dt)
        except (AssertionError,ValueError,struct.error,UnicodeDecodeError):pass
    cfg=None;cs=image.find(b'IKCFG_ST')
    if cs>=0:
        d=zlib.decompressobj(31);raw=d.decompress(image[cs+8:],1024**2);assert d.eof
        assert d.unused_data.startswith(b'IKCFG_ED');(dest/'kernel.config').write_bytes(raw);cfg=dict(offset=cs,sha256=H(raw))
    strings=[m.group().decode('ascii','replace') for m in re.finditer(rb'[ -~]{12,}',image) if any(s in m.group() for s in (b'Linux version',b'initramfs',b'ramdisk',b'initrd',b'Freeing init',b'No working init',b'Failed to execute',b'RAMDISK',b'Unpacking'))]
    report[label]=dict(path=str(src),bytes=len(b),sha256=H(b),header_fields=dict(zip(('kernel_size','kernel_address','ramdisk_size','ramdisk_address','second_size','second_address','tags_address','page_size','dt_size','unused'),fields)),name=b[48:64].rstrip(b'\0').decode(),cmdline=(b[64:576].split(b'\0')[0]+b[608:1632].split(b'\0')[0]).decode(),boot_id_valid=True,kernel_sha256=H(k),kernel_payload_sha256=H(k[512:]),kernel_first128=k[512:640].hex(),kernel_gzip=kernel_gzip,ramdisk_offset=ro,ramdisk_payload_bytes=rs-512,ramdisk_wrapper=ram[:64].hex(),declared_end=ro+align(rs),trailing_bytes=len(b)-ro-align(rs),trailing_nonzero=any(b[ro+align(rs):]),streams=streams,dtbs=dtbs,kernel_config=cfg,kernel_strings=strings,range=dict(ramdisk_start=hex(ra),ramdisk_end=hex(ra+rs),kernel_load_start=hex(ka),kernel_load_end=hex(ka+ks)))
assert kernels['candidate']==kernels['stock']
candidate=(W/sources['candidate'][0]).read_bytes()
report['full_p10']=dict(bytes=16740352,sha256=H(candidate+bytes(16740352-len(candidate))))
assert report['full_p10']['sha256']=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
(R/'evidence'/'image-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'evidence'/'resource-limits.json').write_text(json.dumps(limits,indent=2)+'\n')
print(json.dumps({label:{k:v for k,v in r.items() if k not in ('streams','dtbs','kernel_strings')} for label,r in report.items()},indent=2))
