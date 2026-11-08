#!/usr/bin/env python3
"""Package the actual full diagnostic Image with the unchanged SD-report ramdisk."""
from pathlib import Path
import ast,difflib,json,shutil,struct
import bootformat as b
from fdt import parse
R=Path(__file__).resolve().parents[1];W=R.parent;OLD=W/'2026-11-07-asus-retained-trace-kernel-probe'
CMD=b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1'
PREVIOUS='a0e4856da4138dd401461add3104005fca67cf495da1a605c02392244dd757f8'
def rec(x):return dict(bytes=len(x),sha256=b.sha(x))
def block(s,n):
 lines=s.splitlines(True);a=next(x for x in ast.parse(s).body if getattr(x,'name',None)==n)
 return ''.join(lines[a.lineno-1:a.end_lineno])
def chosen(dt):
 h,nodes,tokens=parse(dt)
 changes={'bootargs':CMD+b'\0','linux,initrd-start':bytes.fromhex('44000000'),'linux,initrd-end':bytes.fromhex('4404e898')}
 strings=bytearray(dt[h[3]:h[3]+h[8]]);tail=dt[h[3]+h[8]:]
 def prop(n,v):
  encoded=n.encode()+b'\0';off=strings.find(encoded)
  if off<0:off=len(strings);strings.extend(encoded)
  return struct.pack('>III',3,len(v),off)+v+bytes(-len(v)%4)
 stream=bytearray();seen=set()
 for t,node,name,value,raw in tokens:
  if t==3 and node=='/chosen' and name in changes:stream+=prop(name,changes[name]);seen.add(name)
  elif t==2 and node=='/chosen':
   for n,v in changes.items():
    if n not in seen:stream+=prop(n,v)
   stream+=raw
  else:stream+=raw
 ah=list(h);ah[3]=h[2]+len(stream);ah[9]=len(stream);ah[8]=len(strings);ah[1]=ah[3]+len(strings)+len(tail)
 new=struct.pack('>10I',*ah)+dt[40:h[2]]+stream+strings+tail
 expected={n:dict(p) for n,p in nodes.items()};expected['/chosen'].update(changes)
 assert parse(new)[1]==expected and new[40:h[2]]==dt[40:h[2]]
 assert [raw for t,n,p,v,raw in parse(new)[2] if n!='/chosen']==[raw for t,n,p,v,raw in tokens if n!='/chosen']
 return new

def main():
 build=json.loads((R/'evidence/build-receipt.json').read_text())
 image_input=(R/'artifacts/Image.gz-dtb').read_bytes()
 assert rec(image_input)==build['artifacts']['arch/arm64/boot/Image.gz-dtb']
 assert rec((R/'artifacts/resolved.config').read_bytes())==build['artifacts']['.config']
 template=(OLD/'artifacts/candidate.img').read_bytes()
 assert b.sha(template)=='189b64559cb8bb961301b54d21f4f2eafab84ef3494268635973c47b387811eb'
 header,kernel,ramdisk,extra=b.parse_image(template);assert not extra
 assert b.sha(ramdisk)=='51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46'
 raw,dt=b.ungzip(image_input);stream=image_input[:-len(dt)]
 assert rec(raw)==build['artifacts']['arch/arm64/boot/Image']
 for marker in [b'ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init',b'ASUS-e9-retained-v2 01 paging_init returned; trace ready',b'05 before time_init',b'06 time_init returned']:assert marker in raw
 assert build['release'].strip()=='#define UTS_RELEASE "4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty"'
 assert b'4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty' in raw
 cp,rem=b.ungzip(ramdisk[512:]);assert not rem
 init=b.parse_cpio(cp)['init'][3];b.elf_static(init)
 assert b'dbbb6afb-dd70-4c35-961e-9c977d7164a8\n' in init and b'PROBE.TXT' in init
 assert len(ramdisk)-512==0x4e898
 newdt=chosen(dt);newkernel=b.wrap(kernel,stream+newdt)
 nh=bytearray(header);nh[64:576]=CMD+bytes(512-len(CMD))
 image=b.make_image(nh,newkernel,ramdisk);full=image+bytes(b.PARTITION_SIZE-len(image))
 (R/'artifacts/candidate.img').write_bytes(image)
 ah,ak,ar,ae=b.parse_image((R/'artifacts/candidate.img').read_bytes());actual_raw,adt=b.ungzip(ak[512:])
 assert not ae and ar==ramdisk and actual_raw==raw and adt==newdt and ak[512:-len(adt)]==stream
 assert ak[:4]==kernel[:4] and ak[8:512]==kernel[8:512]
 assert ah[:8]==header[:8] and ah[12:64]==header[12:64] and ah[608:]==header[608:]
 assert ah[64:576]==CMD+bytes(512-len(CMD)) and not any(ah[608:1632])
 before,after=parse(dt)[1],parse(adt)[1]
 delta=sorted([n,p] for n in before.keys()|after.keys() for p in before.get(n,{}).keys()|after.get(n,{}).keys() if before.get(n,{}).get(p)!=after.get(n,{}).get(p))
 assert delta==[['/chosen','bootargs'],['/chosen','linux,initrd-end'],['/chosen','linux,initrd-start']]
 assert after['/chosen']['bootargs']==CMD+b'\0' and b'initrd=' not in CMD
 assert full==image+bytes(b.PARTITION_SIZE-len(image))
 original=(OLD/'source/install.py').read_text();installer=original
 edits={"IMAGE_SHA='189b64559cb8bb961301b54d21f4f2eafab84ef3494268635973c47b387811eb'":f"IMAGE_SHA='{b.sha(image)}'",
 "FULL_SHA='553fae1260272ef5f161a0a468cb4c5683f8ab479db29c3ba7df82d97a8eb481'":f"FULL_SHA='{b.sha(full)}'",
 "'5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453')":f"'5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453','{PREVIOUS}')",
 "len(image)==8044544":f"len(image)=={len(image)}",
 "profile='exact-linux49-retained-trace-microsd-probe'":"profile='exact-linux49-early-retained-microsd-probe'"}
 for x,y in edits.items():assert installer.count(x)==1;installer=installer.replace(x,y)
 for name in ['execute','Transport']:assert block(original,name)==block(installer,name)
 (R/'source/install.py').write_text(installer)
 (R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True),fromfile='retained-trace/source/install.py',tofile='source/install.py')))
 adapters={}
 for n in ['adb','legacy_adb.py']:
  shutil.copy2(OLD/'source'/n,R/'source'/n);assert (R/'source'/n).read_bytes()==(OLD/'source'/n).read_bytes();adapters[n]=rec((R/'source'/n).read_bytes())
 receipt=dict(status='EARLY_CHECKPOINT_FULL_COMPILE_PACKAGED_NO_PHYSICAL_TRIAL',image=rec(image),full_p10=rec(full),compiled_Image_gz_dtb=rec(image_input),compressed_Image=rec(stream),decompressed_Image=rec(raw),dt_before=rec(dt),dt_after=rec(adt),wrapped_kernel=rec(ak),wrapped_ramdisk=rec(ar),ramdisk_cpio=rec(cp),init=rec(init),header_fields=list(struct.unpack_from('<10I',ah,8)),android_id_hex=ah[576:608].hex(),header_cmdline=CMD.decode(),chosen_bootargs=CMD.decode(),initrd_start='0x44000000',initrd_end='0x4404e898',dt_changes=delta,run_id='dbbb6afb-dd70-4c35-961e-9c977d7164a8',report='PROBE.TXT',lifecycle_seconds=60,preservation=dict(new_compiled_Image_stream_byte_equal=True,new_compiled_raw_Image_byte_equal=True,new_DT_only_chosen_metadata_changed=True,ramdisk_and_static_helper_byte_equal=True,MTK_wrappers_only_kernel_length_changed=True,header_only_kernel_size_cmdline_id_changed=True,execute_and_Transport_byte_equal=True,legacy_adapters=adapters),installer_edits=list(edits.keys()),only_added_known_full_preimage=PREVIOUS,hardware_contact=False,physical_boot_proven=False,flash_go=False)
 (R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(dict(image=rec(image),full_p10=rec(full))))
if __name__=='__main__':main()
