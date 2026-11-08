"""Resolve BTF string offsets; normalize only two pinned spellings of identical source."""
from pathlib import Path
import hashlib,struct
SOURCE_SHA='71566db1d1609edded3261b5557fe1f62eea7f5387264105c8ddbec0a8f9ab84'
SOURCE='hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c'
REFERENCE='/srv/android/asus-linux49-power-supply-filter-20261106/snapshot/'+SOURCE

def canonical_btf(sections):
    for p in (Path('/srv/android/lineage24')/SOURCE,Path(REFERENCE)):
        assert hashlib.sha256(p.read_bytes()).hexdigest()==SOURCE_SHA,'BTF source filename normalization requires identical pinned source bytes'
    data=sections['.BTF'];h=struct.unpack_from('<HBBIIIII',data)
    assert h[:4]==(0xeb9f,1,0,24)
    types=data[h[3]+h[4]:h[3]+h[4]+h[5]]
    strings=data[h[3]+h[6]:h[3]+h[6]+h[7]]
    assert h[3]+h[6]+h[7]==len(data)
    def name(offset):
        assert 0<=offset<len(strings)
        value=strings[offset:strings.index(b'\0',offset)].decode()
        return SOURCE if value in (SOURCE,REFERENCE) else value
    normalized_strings=[SOURCE if x.decode() in (SOURCE,REFERENCE) else x.decode() for x in strings.split(b'\0')]
    records=[];at=0
    def words(count):
        nonlocal at
        value=struct.unpack_from('<'+'I'*count,types,at);at+=4*count;return value
    while at<len(types):
        n,info,size=words(3);kind=(info>>24)&31;vlen=info&0xffff
        extra=[]
        if kind in (0,2,7,8,9,10,11,12,16,18):pass
        elif kind in (1,14,17):extra=list(words(1))
        elif kind==3:extra=list(words(3))
        elif kind in (4,5):
            for _ in range(vlen):
                n,t,o=words(3);extra.append([name(n),t,o])
        elif kind==6:
            for _ in range(vlen):
                n,v=words(2);extra.append([name(n),v])
        elif kind==13:
            for _ in range(vlen):
                n,t=words(2);extra.append([name(n),t])
        elif kind==15:
            for _ in range(vlen):extra.append(list(words(3)))
        elif kind==19:
            for _ in range(vlen):
                n,lo,hi=words(3);extra.append([name(n),lo,hi])
        else:raise AssertionError('Unproved BTF kind '+str(kind))
        records.append([info,size,extra])
    assert at==len(types)
    # Parse headers again with their exact span to retain all header name references.
    at=0;named=[]
    for info,size,extra in records:
        header_name=struct.unpack_from('<I',types,at)[0]
        kind=(info>>24)&31;vlen=info&0xffff
        count={0:0,1:1,2:0,3:3,4:3*vlen,5:3*vlen,6:2*vlen,7:0,8:0,9:0,10:0,11:0,12:0,13:2*vlen,14:1,15:3*vlen,16:0,17:1,18:0,19:3*vlen}[kind]
        named.append([name(header_name),info,size,extra]);at+=12+4*count
    ext=sections['.BTF.ext'];eh=struct.unpack_from('<HBBIIIIIII',ext)
    assert eh[:4]==(0xeb9f,1,0,32)
    def extension(offset,length,kind):
        if not length:return []
        blob=ext[eh[3]+offset:eh[3]+offset+length]
        recsize=struct.unpack_from('<I',blob)[0];pos=4;result=[]
        assert recsize=={'func':8,'line':16,'core':16}[kind]
        while pos<len(blob):
            sec,count=struct.unpack_from('<II',blob,pos);pos+=8;rows=[]
            for _ in range(count):
                values=list(struct.unpack_from('<'+'I'*(recsize//4),blob,pos));pos+=recsize
                if kind=='line':values[1]=name(values[1]);values[2]=name(values[2])
                elif kind=='core':values[2]=name(values[2])
                rows.append(values)
            result.append([name(sec),rows])
        assert pos==len(blob)
        return result
    assert eh[3]+eh[8]+eh[9]==len(ext)
    return {'btf_header_except_string_length':list(h[:7]),'strings':normalized_strings,'types':named,
      'ext_header':list(eh),'func':extension(eh[4],eh[5],'func'),'line':extension(eh[6],eh[7],'line'),'core':extension(eh[8],eh[9],'core')}
