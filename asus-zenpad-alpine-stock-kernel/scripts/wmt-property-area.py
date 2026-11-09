#!/usr/bin/env python3
"""One stock-format WMT readiness property; no service or chip-ID override."""
from pathlib import Path
import argparse, os, struct
NAME='service.wcn.driver.ready'

def make_area(value):
    assert value in ('no','yes')
    data=bytearray()
    def allocate(size):
        offset=len(data)
        data.extend(bytes((size+3)&~3))
        return offset
    root=allocate(21)
    parent=root
    for component in NAME.split('.'):
        encoded=component.encode()
        node=allocate(21+len(encoded))
        struct.pack_into('<I',data,parent+16,node)
        struct.pack_into('<I',data,node,len(encoded))
        data[node+20:node+20+len(encoded)]=encoded
        parent=node
    encoded=NAME.encode(); payload=value.encode()
    prop=allocate(96+len(encoded)+1)
    struct.pack_into('<I',data,parent+4,prop)
    struct.pack_into('<I',data,prop,len(payload)<<24)
    data[prop+4:prop+4+len(payload)]=payload
    data[prop+96:prop+96+len(encoded)]=encoded
    area=bytearray(4096)
    struct.pack_into('<4I',area,0,len(data),0,0x504f5250,0xfc6ed0ab)
    area[128:128+len(data)]=data
    return bytes(area)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ready',required=True,choices=['no','yes'])
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    blob=make_area(a.ready)
    temporary=a.output.with_name(a.output.name+'.partial')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
    with os.fdopen(fd,'wb') as f:
        f.write(blob)
        if os.geteuid()==0:os.fchown(f.fileno(),0,0)
        os.fchmod(f.fileno(),0o444)
    os.replace(temporary,a.output)
if __name__=='__main__':main()
