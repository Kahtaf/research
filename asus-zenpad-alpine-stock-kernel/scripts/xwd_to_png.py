#!/usr/bin/env python3
"""Convert this trial's validated 32-bit XWD ZPixmap to a standalone PNG."""
from pathlib import Path
import struct, sys, zlib
src,dst=map(Path,sys.argv[1:])
b=src.read_bytes(); h=struct.unpack('>25I',b[:100])
(header,version,fmt,depth,w,he,xoff,byteorder,unit,bitorder,pad,bpp,stride,visual,rm,gm,bm,bits,entries,ncolors,*_)=h
assert version==7 and fmt==2 and bpp in (24,32) and xoff==0
pixel_bytes=bpp//8
assert 0<w<=4096 and 0<he<=4096 and stride>=w*pixel_bytes
assert byteorder in (0,1)
start=header+ncolors*12
assert len(b)>=start+stride*he
masks=[rm,gm,bm]
shifts=[(m&-m).bit_length()-1 for m in masks]
assert all((m>>s)==255 for m,s in zip(masks,shifts))
raw=bytearray()
for y in range(he):
 raw.append(0)
 for x in range(w):
  pos=start+y*stride+x*pixel_bytes
  pix=int.from_bytes(b[pos:pos+pixel_bytes],'little' if byteorder==0 else 'big')
  raw.extend((pix>>s)&255 for s in shifts)
def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,he,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,3))+chunk(b'IEND',b'')
dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(png)
print(str(dst),w,he)
