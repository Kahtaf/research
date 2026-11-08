"""One offline package of the actual built kernel and unchanged USB reporter."""
from pathlib import Path
import ast,difflib,json,shutil,struct
import bootformat as b
from fdt import parse
R=Path(__file__).resolve().parents[1];W=R.parent;OLD=W/'2026-11-07-asus-uart-fixed-usb-pid1-report'
CMD=b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1'
PREVIOUS='c1fe664108ee8e2ef24edc9f0b3249589dc227f0ee8502b63e224930ee7fa541'
def rec(x):return dict(bytes=len(x),sha256=b.sha(x))
def block(s,n):
 a=next(x for x in ast.parse(s).body if getattr(x,'name',None)==n)
 return ''.join(s.splitlines(True)[a.lineno-1:a.end_lineno])
def chosen(dt):
 h,nodes,tokens=parse(dt)
 changes={'bootargs':CMD+b'\0','linux,initrd-start':bytes.fromhex('44000000'),'linux,initrd-end':bytes.fromhex('4403e4a3')}
 strings=bytearray(dt[h[3]:h[3]+h[8]]);tail=dt[h[3]+h[8]:]
 def prop(n,v):
  encoded=n.encode()+b'\0';off=strings.find(encoded)
  if off<0:off=len(strings);strings.extend(encoded)
  return struct.pack('>III',3,len(v),off)+v+bytes(-len(v)%4)
 stream=bytearray();seen=set()
 for t,node,name,value,token in tokens:
  if t==3 and node=='/chosen' and name in changes:stream+=prop(name,changes[name]);seen.add(name)
  elif t==2 and node=='/chosen':
   for n,v in changes.items():
    if n not in seen:stream+=prop(n,v)
   stream+=token
  else:stream+=token
 ah=list(h);ah[3]=h[2]+len(stream);ah[9]=len(stream);ah[8]=len(strings);ah[1]=ah[3]+len(strings)+len(tail)
 new=struct.pack('>10I',*ah)+dt[40:h[2]]+stream+strings+tail
 expected={n:dict(p) for n,p in nodes.items()};expected['/chosen'].update(changes)
 assert parse(new)[1]==expected and new[40:h[2]]==dt[40:h[2]]
 ignored=lambda t:t[1]=='/chosen' and t[2] in changes
 assert [t for t in parse(new)[2] if not ignored(t)]==[t for t in tokens if not ignored(t)]
 return new

def main():
 assert not (R/'artifacts/candidate.img').exists(),'One package only'
 build=json.loads((R/'evidence/build-receipt.json').read_text())
 compiled=(R/'artifacts/Image.gz-dtb').read_bytes();config=(R/'artifacts/resolved.config').read_bytes()
 assert rec(compiled)==build['artifacts']['arch/arm64/boot/Image.gz-dtb']
 assert rec(config)==build['artifacts']['.config']==dict(bytes=126443,sha256='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1')
 template=(OLD/'artifacts/candidate.img').read_bytes()
 assert rec(template)==dict(bytes=7970816,sha256='8298badb09d9e91ee584eb6e27baf2054e660bbc5640443e9212f484f6fd590b')
 assert b.sha(template+bytes(b.PARTITION_SIZE-len(template)))==PREVIOUS
 header,oldkernel,ramdisk,extra=b.parse_image(template);assert not extra
 assert rec(ramdisk)==dict(bytes=255651,sha256='51e6d1dc0acb742522c69b29355d2d77d8ba73a3597fb8ad3354fa9f0c494e49')
 assert header[64:576]==CMD+bytes(512-len(CMD))
 cp,rem=b.ungzip(ramdisk[512:]);assert not rem
 init=b.parse_cpio(cp)['init'][3];elf=b.elf_static(init)
 assert rec(init)==dict(bytes=597856,sha256='d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b')
 for marker in [b'9342cbf1-3bf0-44d4-b655-a1ca30146a99',b'P499342cbf13bf044d4b655',b'ASUS-PID1:%s',b'PROBE   TXT']:assert marker in init
 raw,dt=b.ungzip(compiled);stream=compiled[:-len(dt)]
 assert rec(raw)==build['artifacts']['arch/arm64/boot/Image']
 baseline=(W/'2026-11-07-asus-early-uart-disabled-kernel/artifacts/Image.gz-dtb').read_bytes()
 assert b.sha(baseline)=='063dad1d9cc03b1c335dd712c9fcb0c36a006e5e99ebee4577e73e669613ac2d'
 assert dt==b.ungzip(baseline)[1],'No DT source changes permitted'
 for marker in [b'ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init',b'ASUS-e9-retained-v2 01 paging_init returned; trace ready',b'05 before time_init',b'06 time_init returned']:assert marker in raw
 newdt=chosen(dt)
 assert newdt==b.ungzip(oldkernel[512:])[1],'Packaged DT must equal existing USB reporter DT'
 newkernel=b.wrap(oldkernel,stream+newdt)
 image=b.make_image(header,newkernel,ramdisk);full=image+bytes(b.PARTITION_SIZE-len(image))
 assert len(full)==16740352
 (R/'artifacts/candidate.img').write_bytes(image)
 ah,ak,ar,ae=b.parse_image((R/'artifacts/candidate.img').read_bytes());actual_raw,adt=b.ungzip(ak[512:])
 assert not ae and ar==ramdisk and actual_raw==raw and adt==newdt and ak[512:-len(adt)]==stream
 assert ak[:4]==oldkernel[:4] and ak[8:512]==oldkernel[8:512]
 assert ah[:8]==header[:8] and ah[12:576]==header[12:576] and ah[608:]==header[608:]
 original=(OLD/'source/install.py').read_text();installer=original
 edits={"IMAGE_SHA='8298badb09d9e91ee584eb6e27baf2054e660bbc5640443e9212f484f6fd590b'":f"IMAGE_SHA='{b.sha(image)}'",f"FULL_SHA='{PREVIOUS}'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7970816':f'len(image)=={len(image)}',"profile='exact-linux49-uart-fixed-ram-usb-pid1-report'":"profile='exact-linux49-early-watchdog-handoff-ram-usb-pid1-report'","'e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0')":f"'e965b75979e02e5514418e706f42b7874e4f72d72754864e5af0959646d2c9b0','{PREVIOUS}')"}
 for old,new in edits.items():assert installer.count(old)==1;installer=installer.replace(old,new)
 for name in ['execute','Transport','Guard']:assert block(original,name)==block(installer,name)
 (R/'source/install.py').write_text(installer)
 (R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True),fromfile='uart-fixed-usb/source/install.py',tofile='watchdog-handoff/source/install.py')))
 adapters={}
 for n in ['adb','legacy_adb.py']:
  shutil.copy2(OLD/'source'/n,R/'source'/n);assert (R/'source'/n).read_bytes()==(OLD/'source'/n).read_bytes();adapters[n]=rec((R/'source'/n).read_bytes())
 (R/'artifacts/ramdisk.wrapped').write_bytes(ramdisk);(R/'artifacts/init').write_bytes(init)
 before,after=parse(dt)[1],parse(adt)[1]
 delta=sorted([n,p] for n in before.keys()|after.keys() for p in before.get(n,{}).keys()|after.get(n,{}).keys() if before.get(n,{}).get(p)!=after.get(n,{}).get(p))
 assert delta==[['/chosen','bootargs'],['/chosen','linux,initrd-end'],['/chosen','linux,initrd-start']]
 assert struct.unpack_from('<I',ramdisk,4)[0]==len(ramdisk)-512==0x3e4a3
 receipt=dict(status='PACKAGED_NO_INSTALL_OR_PHYSICAL_GO',image=rec(image),full_p10=rec(full),full_p10_remote_path='/srv/android/asus-early-watchdog-handoff-20261107/artifacts/candidate.p10.raw',input_template=rec(template),compiled_Image_gz_dtb=rec(compiled),config=rec(config),compressed_Image=rec(stream),decompressed_Image=rec(raw),dt_before=rec(dt),dt_after=rec(adt),wrapped_kernel=rec(ak),wrapped_ramdisk=rec(ar),init=rec(init),elf=elf,dt_changes=delta,cmdline=CMD.decode(),initrd_start='0x44000000',initrd_end='0x4403e4a3',run_id='9342cbf1-3bf0-44d4-b655-a1ca30146a99',usb_serial='P499342cbf13bf044d4b655',usb=dict(vid='0b05',pid='4a49',product='ASUS-PID1:<actual uname.release>',fresh_host_absence_required=True),lifecycle_seconds=60,lifecycle='Existing SIGALRM/monotonic lifecycle byte-preserved; automatic return unproved',preservation=dict(compiled_gzip_byte_equal=True,compiled_raw_Image_byte_equal=True,DT_source_identical_to_baseline=True,DT_packaged_identical_to_existing_USB_candidate=True,DT_only_inherited_chosen_metadata_changed=True,ramdisk_and_static_init_byte_equal=True,header_only_kernel_size_and_ID_changed=True,kernel_wrapper_only_payload_length_changed=True,execute_Transport_Guard_byte_equal=True,legacy_adapters=adapters),installer=rec(installer.encode()),installer_edits=edits,only_added_known_full_preimage=PREVIOUS,parent_install_run='ffcb0e5d-a976-4723-9f17-133910fb75d9',init_compilation=False,hardware_contact=False,physical_boot_proven=False,flash_go=False)
 (R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(dict(image=rec(image),full_p10=rec(full))))
if __name__=='__main__':main()
