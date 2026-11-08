from pathlib import Path
import sys,hashlib,struct,gzip,json,ast,difflib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
sha=b.sha
assert not (R/'evidence/packaging-receipt.json').exists()
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
donor=W/'2026-11-07-asus-stock-legacy-ram-usb-reporter'
data=(donor/'artifacts/candidate.img').read_bytes();assert sha(data)=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
h,k,r,t=b.parse_image(data);assert not t
raw,dt=b.ungzip(k[512:]);assert sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
base=0xffffffc000080000;target=0xffffffc0006976c8;call=0xffffffc000800278
patches=[(0xffffffc00080026c,bytes.fromhex('00800d91'),struct.pack('<I',0x52800000|(0xa7<<5))),(call,bytes.fromhex('4cf90a94'),struct.pack('<I',0x94000000|(((target-call)//4)&0x3ffffff)))]
new=bytearray(raw)
for a,old,v in patches:
 assert raw[a-base:a-base+4]==old;new[a-base:a-base+4]=v
assert {i//4 for i,(x,y) in enumerate(zip(raw,new)) if x!=y}=={(a-base)//4 for a,_,_ in patches}
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
before=list(md.disasm(raw[0x780260:0x7802a8],base+0x780260));after=list(md.disasm(bytes(new)[0x780260:0x7802a8],base+0x780260))
assert next(i for i in after if i.address==patches[0][0]).op_str=='w0, #0xa7'
assert next(i for i in after if i.address==call).op_str==hex(target).replace('0x','#0x')
stream=k[512:-len(dt)];gz=bytearray(gzip.compress(bytes(new),compresslevel=9,mtime=0));assert stream[:3]==gz[:3] and stream[3]==0
# Preserve original gzip metadata, deflate stream is regenerated at level 9.
assert len(stream[:10])==10 and stream[8]==2
gz[:10]=stream[:10]
nk=b.wrap(k,bytes(gz)+dt);image=b.make_image(h,nk,r);full=image+bytes(b.PARTITION_SIZE-len(image))
ah,ak,ar,at=b.parse_image(image);nr,nd=b.ungzip(ak[512:]);assert nr==new and nd==dt and ar==r and not at
assert ah[12:16]==h[12:16] and ah[16:576]==h[16:576] and ah[608:]==h[608:]
assert ak[:4]==k[:4] and ak[8:512]==k[8:512]
cp,extra=b.ungzip(r[512:]);assert not extra
init=b.parse_cpio(cp)['init'][3];elf=b.elf_static(init)
for name in ('adb','legacy_adb.py','bootformat.py'):
 value=(donor/'source'/name).read_bytes();(R/'source'/name).write_bytes(value);assert (R/'source'/name).read_bytes()==value
original=(W/'2026-11-07-asus-linux49-failure-log-package/source/install.py').read_text()
line=next(x for x in original.splitlines() if x.startswith('INSTALL_PREIMAGES='))
current='0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d';assert current not in line
edits={"IMAGE_SHA='cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265'":f"IMAGE_SHA='{sha(image)}'",f"FULL_SHA='{current}'":f"FULL_SHA='{sha(full)}'",'len(image)==7974912':f'len(image)=={len(image)}',"profile='exact-linux49-unchanged-kernel-configfs-failure-log-r1'":"profile='stock-3.18.35-scalar-a7-legacy-ram-usb-control-r1'",line:line[:-1]+f",'{current}')"}
installer=original
for x,y in edits.items():assert installer.count(x)==1;installer=installer.replace(x,y)
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name);return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
for name in ('execute','Transport','Guard'):assert block(original,name)==block(installer,name)
reverse=installer
for x,y in reversed(list(edits.items())):assert reverse.count(y)==1;reverse=reverse.replace(y,x)
assert reverse==original
(R/'source/install.py').write_text(installer)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True))))
(R/'artifacts/candidate.img').write_bytes(image);(R/'artifacts/candidate.p10.raw').write_bytes(full)
rec=lambda x:dict(bytes=len(x),sha256=sha(x))
receipt=dict(status='LOCAL_PACKAGED_NO_PHYSICAL_GO',expected_tag=167,candidate=rec(image),full_p10=rec(full),donor=rec(data),raw_before=rec(raw),raw_after=rec(new),ramdisk=rec(r),init=rec(init),init_elf=elf,dt=rec(dt),gzip_header_before=stream[:10].hex(),gzip_header_after=bytes(gz[:10]).hex(),gzip_settings='level 9, original ten-byte gzip header metadata',patches=[dict(address=hex(a),raw_offset=hex(a-base),before=old.hex(),after=v.hex()) for a,old,v in patches],preservation=dict(exact_two_instruction_words=True,ramdisk_entire=True,helper_ELF=True,appended_DT=True,header_addresses_bootargs=True,kernel_wrapper_except_length=True,execute_Transport_Guard_byte_identical=True,legacy_adapters_byte_identical=True,original_admissions_preserved=True),runtime_route_evidence_sha256=sha((R/'evidence/runtime-route.json').read_bytes()),limitations='Expected previously observed normal reset route; may be bypassed. Setter init/pointer guards, persistence/cache flush/snapshot identity remain uncalibrated. No automatic return proof for modified image; no absence implies nonexecution.',scope=dict(device=False,network=False,private=False,kernel_compile=False,physical_GO=False))
(R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'evidence/patched-handler.disasm').write_text('\n'.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in after)+'\n')
print(json.dumps(receipt,indent=2))
