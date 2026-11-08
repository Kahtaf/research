from pathlib import Path
import subprocess,struct,json,hashlib,sys,re
R=Path('/srv/android/asus-linux49-entry-text-checkpoint-20261107');B=Path('/srv/android/asus-early-watchdog-handoff-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
assert not (E/'linked-entry.json').exists(), 'One linked-artifact check'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
copy=json.loads((E/'source-copy.json').read_text());uploaded=json.loads((E/'build-launch.json').read_text())['uploaded']
for n,pin in copy['selected_baseline'].items():
 assert sha(B/'kernel'/n)==pin
 assert sha(K/n)==uploaded.get('kernel/'+n,pin)
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03'
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes()
extra=['drivers/clocksource/arm_arch_timer.c','drivers/clocksource/mtk_apxgpt.c','drivers/tty/serial/8250/8250_mtk.c','drivers/misc/mediatek/uart/uart.c','drivers/misc/mediatek/rtc/mtk_rtc.c']
hardware={n:sha(K/n) for n in extra if (K/n).is_file()}
for n,pin in hardware.items():assert sha(B/'kernel'/n)==pin
for n,pin in uploaded.items():assert sha(R/n)==pin
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True)
symbols={l.split()[2]:int(l.split()[0],16) for l in nm.splitlines() if len(l.split())==3}
names=['_text','_end','stext','preserve_boot_args','el2_setup','asus_entry_text_begin','asus_entry_text_end','asus_entry_text_commit','asus_entry_tag','asus_entry_tag_end','asus_entry_expected_dtb','asus_entry_expected_dtb_end','asus_retained_trace_early_init','asus_retained_trace_init']
s={n:symbols[n] for n in names};raw=(O/'arch/arm64/boot/Image').read_bytes()
read=lambda a,z:raw[a-s['_text']:z-s['_text']]
assert s['stext']==s['asus_entry_text_begin']
header_offset=4 if struct.unpack_from('<I',raw)[0]==0x91005a4d else 0
head=struct.unpack_from('<I',raw,header_offset)[0];assert head&0xfc000000==0x14000000
imm=head&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm
assert s['_text']+header_offset+4*imm==s['stext']
end=s['asus_entry_text_end'];words=struct.unpack('<2I',read(end,end+8))
for at,word,target in [(end,words[0],s['preserve_boot_args']),(end+4,words[1],s['el2_setup'])]:
 assert word&0xfc000000==0x94000000
 imm=word&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm
 assert at+4*imm==target
identity=json.loads((R/'source/identity.json').read_text());tag=identity['tag'].encode()
assert read(s['asus_entry_tag'],s['asus_entry_tag_end'])==tag
expected=(R/'source/expected-runtime.dtb').read_bytes()
assert read(s['asus_entry_expected_dtb'],s['asus_entry_expected_dtb_end'])==expected
release=(O/'include/generated/utsrelease.h').read_text().split('"')[1];assert 'release='+release+' ' in identity['tag']
assert read(s['asus_entry_text_commit'],s['asus_entry_text_commit']+8)==bytes.fromhex('913800b99f3f03d5'), 'str w17,[x4,#0x38]; dsb sy'
code=read(s['asus_entry_text_begin'],s['asus_entry_text_end'])
dis=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(s['stext']),'--stop-address='+hex(end+12),str(O/'vmlinux')],text=True)
(E/'entry.disasm').write_text(dis)
instructions=[]
for line in dis.splitlines():
 m=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)',line)
 if m and s['stext']<=int(m[1],16)<end:instructions.append(m[3])
# x0 is read-only as FDT; x1..x3, x18..x30 and SP must not occur at all.
assert not any(re.search(r'\b(?:sp|[xw](?:[1-3]|1[89]|2[0-9]|30))\b',a.split('//')[0]) for a in instructions)
assert not any(a.split()[0] in ['bl','blr','ret','stp','ldp'] for a in instructions)
assert not any(re.match(r'\w+\s+[xw]0\s*,',a) and a.split()[0] not in ('cmp','tst') for a in instructions)
commit=(s['asus_entry_text_commit']-s['asus_entry_text_begin'])//4
assert instructions[commit].split()[0]=='str'
assert instructions[commit+1].startswith('dsb')
# The original watchdog initcall level/order and early UART absence are checked once.
sys.path.insert(0,str(B/'scripts'))
from initcall_evidence import analyze
initcalls=analyze(O/'vmlinux',3);assert not (O/'drivers/tty/serial/8250/8250_early.o').exists()
(E/'compiled-initcalls.json').write_text(json.dumps(initcalls,indent=2)+'\n')
result=dict(status='LINKED_ENTRY_ABI_AND_PRESERVATION_CHECK_PASSED',symbols={n:hex(v) for n,v in s.items()},entry_code_bytes=len(code),entry_code_sha256=hashlib.sha256(code).hexdigest(),entry_code_hex=code.hex(),commit_bytes=read(s['asus_entry_text_commit'],s['asus_entry_text_commit']+8).hex(),tag=identity['tag'],tag_bytes=len(tag),tag_sha256=hashlib.sha256(tag).hexdigest(),expected_runtime_dtb_sha256=hashlib.sha256(expected).hexdigest(),release=release,entry_before_original_boot_args_EL_MMU_calls=True,head_branch_target='stext == asus_entry_text_begin',LR_SP_and_boot_arguments_preserved=True,no_calls_stack_or_mutable_globals=True,selected_old_source_and_baseline_Image_unchanged=True,selected_new_sources_match_uploaded_hashes=True,extra_hardware_equal=hardware,config_byte_identical=True,no_early_UART=True,watchdog_initcall_unchanged=True,physical_execution=False,absence='UNKNOWN')
(E/'linked-entry.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='entry_code_hex'},indent=2))
