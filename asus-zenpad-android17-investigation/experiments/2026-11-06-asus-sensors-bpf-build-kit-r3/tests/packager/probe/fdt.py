"""Bounded FDT property update preserving every other token and reservation."""
import struct

def parse(data):
    h=struct.unpack_from('>10I',data)
    assert h[0]==0xd00dfeed and h[1]==len(data) and h[5]==17 and h[6]<=17
    assert 40<=h[4]<h[2] and h[2]+h[9]==h[3] and h[3]+h[8]<=len(data)
    strings=data[h[3]:h[3]+h[8]];pos=h[2];stack=[];nodes={};tokens=[]
    while pos<h[2]+h[9]:
        start=pos;t=struct.unpack_from('>I',data,pos)[0];pos+=4;name=None;value=None
        if t==1:
            end=data.index(0,pos);stack.append(data[pos:end].decode());pos=(end+4)&~3
            nodes['/'.join(stack)]={}
        elif t==3:
            size,off=struct.unpack_from('>II',data,pos);pos+=8
            assert off<len(strings)
            name=strings[off:strings.index(0,off)].decode();value=data[pos:pos+size]
            assert len(value)==size;pos=(pos+size+3)&~3
            assert name not in nodes['/'.join(stack)];nodes['/'.join(stack)][name]=value
        elif t not in (2,4,9):raise ValueError(t)
        tokens.append((t,'/'.join(stack),name,value,data[start:pos]))
        if t==2:stack.pop()
        if t==9:
            assert not stack and pos==h[2]+h[9];break
    return h,nodes,tokens

def exact_initrd(data,start,length,extra_args=b''):
    h,nodes,tokens=parse(data);assert '/chosen' in nodes and length>0
    strings=bytearray(data[h[3]:h[3]+h[8]])
    args=nodes['/chosen']['bootargs'].rstrip(b'\0').split()
    assert not any(x.startswith(b'initrd=') for x in args),'Refuse inherited initrd override'
    for item in extra_args.split():
        assert not item.startswith(b'initrd=')
        key=item.split(b'=',1)[0]
        matches=[x for x in args if x.split(b'=',1)[0]==key]
        assert not matches or matches==[item],('Conflicting boot argument',item,matches)
        if not matches:args.append(item)
    args.append(f'initrd=0x{start:x},0x{length:x}'.encode())
    changes={'bootargs':b' '.join(args)+b'\0','linux,initrd-start':struct.pack('>Q',start),'linux,initrd-end':struct.pack('>Q',start+length)}
    def prop(n,v):
        encoded=n.encode()+b'\0';off=strings.find(encoded)
        if off<0:off=len(strings);strings.extend(encoded)
        return struct.pack('>III',3,len(v),off)+v+bytes((-len(v))%4)
    stream=bytearray();seen=set()
    for t,node,name,value,raw in tokens:
        if node=='/chosen' and t==3 and name in changes:
            stream+=prop(name,changes[name]);seen.add(name)
        elif node=='/chosen' and t==2:
            for n,v in changes.items():
                if n not in seen:stream+=prop(n,v)
            stream+=raw
        else:stream+=raw
    header=list(h);header[1]=h[2]+len(stream)+len(strings);header[3]=h[2]+len(stream);header[8]=len(strings);header[9]=len(stream)
    result=struct.pack('>10I',*header)+data[40:h[2]]+stream+strings
    _,after,_=parse(result)
    expected={n:dict(props) for n,props in nodes.items()};expected['/chosen'].update(changes)
    assert after==expected and result[40:h[2]]==data[40:h[2]]
    return bytes(result)
