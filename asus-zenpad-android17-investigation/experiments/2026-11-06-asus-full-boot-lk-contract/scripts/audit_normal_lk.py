#!/usr/bin/env python3
"""Exact binary/CFG pins plus bounded copy model; no CPU emulation or device I/O."""
from collections import deque
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from bootformat import sha
from package_full_boot import components
from lk_contract import LK_DEFAULT
P=ROOT.parent/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin'
data=P.read_bytes();assert sha(data)=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
def raw(addr,n):return data[addr-0x41e00000+512:addr-0x41e00000+512+n]
def string(addr):return raw(addr,1024).split(b'\0')[0]
assert string(0x41e5b964)==LK_DEFAULT
assert string(0x41e41944)==b'ROOTFS'
assert string(0x41e41874)==b'KERNEL'
assert 0x41e1de78+2*struct.unpack('<H',raw(0x41e1de78,2))[0]==0x41e1e070
pins={0x41e1e084:'e6f71af9',0x41e1e0d6:'e7f7edf8',0x41e1e0aa:'e6f79bfb',0x41e1e0ca:'e1e6',
      0x41e0484a:'fff7e5fc',0x41e0485a:'a5f50075',0x41e0486e:'a3f50073',
      0x41e048be:'7844',0x41e048c0:'fff7aafc',0x41e048c8:'2060',0x41e048da:'03f50073',
      0x41e1dea4:'5869',0x41e1deac:'07f086ed',0x41e1dedc:'6421',0x41e1dee0:'07f01cfd',
      0x41e1df54:'8de83000',0x41e1df58:'fff770ff',
      0x41e1cf96:'0335',0x41e1cf9a:'25f00305',0x41e1cfdc:'4ff0e073',
      0x41e1d136:'09f077fd',0x41e1d176:'09f057fd',0x41e1d664:'09f0e0fa'}
for addr,value in pins.items():assert raw(addr,len(bytes.fromhex(value))).hex()==value
# Resolve the actual PC-relative ROOTFS argument, not just string presence.
assert struct.unpack('<I',raw(0x41e04964,4))[0]+0x41e048c2==0x41e41944
lines=(ROOT/'evidence/reachable-disassembly.txt').read_text().splitlines();graph={};functions={};fn=None
for line in lines:
 if line.startswith('FUNCTION '):fn=line.split()[1];functions[fn]=[]
 elif re.match(r'^[0-9a-f]{8} ',line):
  address=int(line[:8],16);encoded=line.split()[1];assert raw(address,len(encoded)//2).hex()==encoded
  edge_text=line.split(' -> ')[1].split(' ; ')[0].strip()
  graph[address]=[int(x,16) for x in edge_text.split(',') if x];functions[fn].append(address)
def path(start,end):
 q=deque([[start]]);seen=set()
 while q:
  p=q.popleft();node=p[-1]
  if node==end:return p
  if node in seen:continue
  seen.add(node)
  for n in graph.get(node,[]):q.append(p+[n])
 raise AssertionError((hex(start),hex(end)))
waypoints=[0x41e1e070,0x41e1e084,0x41e1e094,0x41e1e0d6,0x41e1e0a6,0x41e1e0aa,0x41e1e0ba,0x41e1e0ca,0x41e1de90,0x41e1dea4,0x41e1deac,0x41e1dedc,0x41e1dee0,0x41e1df58]
paths=[list(map(hex,path(a,b))) for a,b in zip(waypoints,waypoints[1:])]
for start,end in [(0x41e047e4,0x41e048c0),(0x41e048c0,0x41e048da),(0x41e048da,0x41e048ee)]:path(start,end)

def recognized(blob,name):
 assert blob[:4]==bytes.fromhex('88168858')
 assert blob[8:40].split(b'\0')[0].lower()==name.lower()
 n=struct.unpack_from('<I',blob,4)[0];assert n==len(blob)-512
 return blob[512:512+n]
results=[]
for p in sorted((ROOT/'artifacts').glob('*/NONBOOTABLE-SYNTHETIC-full-BOOT.img')):
 image=p.read_bytes();h,k,r,cmd=components(image)
 kernel=recognized(k,b'kernel');ram=recognized(r,b'rootfs')
 destination=struct.unpack_from('<I',h,20)[0]
 assert destination==0x44000000 and ram[:2]==b'\x1f\x8b' and len(cmd)<=99
 results.append({'image':str(p.relative_to(ROOT)),'sha256':sha(image),'copied_ramdisk_sha256':sha(ram),'copied_ramdisk_first_bytes':ram[:16].hex(),'actual_destination':hex(destination),'actual_dt_end':hex(destination+len(ram)),'header_copied_without_truncation':True,'header_bytes':len(cmd)})
report={'kind':'PINNED_NORMAL_BOOT_STATIC_REACHABILITY_AND_SEMANTIC_COPY_MODEL_NOT_EXECUTION',
 'lk_sha256':sha(data),'normal_mode_table_entry_0':'0x41e1e070','normal_path_segments':paths,
 'normal_header_call':'0x41e1e084 -> 0x41e042bc','normal_payload_call':'0x41e1e0aa -> 0x41e047e4',
 'normal_loader_ramdisk_name':'ROOTFS','rootfs_argument_resolved_from_literal':True,'binary_pins':{hex(k):v for k,v in pins.items()},
 'lk_default_cmdline':LK_DEFAULT.decode(),'fixtures':results,
 'assumed_boundaries':['valid/loading-accepted header and successful storage reads','preloader 64-bit flag nonzero','ordinary memcpy/snprintf/libfdt contracts','runtime providers do not override initrd/enforcing/hardware/fstab/boot devices','runtime final cmdline fits LK buffer','RAM/framebuffer allocation and secure monitor transfer succeed'],
 'not_proved':['ASUS signature/locked LK acceptance','SMC r2 becomes AArch64 x0','EL/MMU/cache/entry state','actual userspace or hardware boot']}
(ROOT/'evidence/normal-lk-contract.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS exact LK pins, normal-mode reachability, ROOTFS source adjustment, common relocation, 99-byte header, two synthetic fixtures')
