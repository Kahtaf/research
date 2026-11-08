#!/usr/bin/env python3
"""Compare the compiled candidate's memory/GPU metadata with actual live bytes.

This checks artifact metadata, not hardware operation or bootloader fix-ups.
"""
import argparse
import json
import struct
from pathlib import Path

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('dtb',type=Path);a=p.parse_args()
data=a.dtb.read_bytes()
magic,total,off_struct,off_strings=struct.unpack_from('>4I',data)
assert magic==0xd00dfeed and total<=len(data)
nodes={};stack=[];pos=off_struct
while True:
    token,=struct.unpack_from('>I',data,pos);pos+=4
    if token==1:
        end=data.index(0,pos);stack.append(data[pos:end].decode())
        pos=(end+4)&~3;nodes['/'.join(stack) or '/']={}
    elif token==2:
        stack.pop()
    elif token==3:
        length,nameoff=struct.unpack_from('>2I',data,pos);pos+=8
        start=off_strings+nameoff;end=data.index(0,start)
        nodes['/'.join(stack) or '/'][data[start:end].decode()]=data[pos:pos+length]
        pos=(pos+length+3)&~3
    elif token==4:
        continue
    elif token==9:
        break
    else:
        raise ValueError(f'Invalid DT token {token}')

live=root.parent/'2026-11-05-asus-mt8163-kernel-bringup/evidence/live-device-tree'
checks=[]
def same(candidate,observed,prop):
    expected=(live/observed.lstrip('/')/prop).read_bytes()
    assert nodes[candidate][prop]==expected,(candidate,prop)
    checks.append({'node':candidate,'property':prop,'matches_live':True})

memory=[n for n,props in nodes.items() if props.get('device_type')==b'memory\0']
assert memory==['/memory@00000000'],memory
same(memory[0],memory[0],'reg')
for node,observed in [
    ('atf-reserved-memory','atf-reserved-memory@43000000'),
    ('ram_console-reserved-memory','ram_console-reserved-memory@44400000'),
    ('minirdump-reserved-memory','minirdump-reserved-memory@44570000'),
    ('secure-carveout','secure-carveout')]:
    same('/reserved-memory/'+node,'/reserved-memory/'+observed,'reg')
same('/reserved-memory/secure-carveout','/reserved-memory/secure-carveout','alignment')
for prop in ['reg','interrupts','interrupt-names','clock-frequency']:
    same('/soc/gpu@13040000','/soc/gpu@13040000',prop)
for name in ['mdump-reserved-memory','pstore-reserved-memory']:
    assert '/reserved-memory/'+name not in nodes
assert not any('asus,allow-battery-charging' in props for props in nodes.values())
summary={'status':'passed','meaning':'Compiled DT metadata matches selected observed live properties; hardware untested',
    'memory_nodes':memory,'live_property_checks':checks,'battery_charging_permitted':False,
    'dtb_bytes':len(data)}
(root/'evidence/compiled-dt-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(f'{len(checks)} live memory/GPU property comparisons pass; single RAM node; charging inhibited')
