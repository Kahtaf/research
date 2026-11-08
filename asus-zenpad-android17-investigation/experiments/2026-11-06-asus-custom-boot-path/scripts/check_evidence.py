#!/usr/bin/env python3
"""Read saved files only; reproduce bounded LK findings and rollback identity.
No USB, ADB, fastboot, network, subprocesses, writes to source files, or writer.
The JSON output is offline evidence, never evidence of successful hardware boot.
"""
from pathlib import Path
import hashlib,json,struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
root=Path(__file__).resolve().parents[1]; workspace=root.parent
old=workspace/'2026-11-05-asus-boot-access-audit'
data=(old/'sources/firmware/lk.bin').read_bytes()
sha=hashlib.sha256(data).hexdigest()
assert sha=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
base=0x41e00000
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def ins(addr,count):
 return list(md.disasm(data[addr-base+512:addr-base+512+count*4],addr,count))
def word(addr):return struct.unpack_from('<I',data,addr-base+512)[0]
def expect(addr,expected):
 actual=ins(addr,len(expected))
 assert [(i.mnemonic,i.op_str) for i in actual]==expected,(hex(addr),[(i.mnemonic,i.op_str) for i in actual])
 return [{'address':hex(i.address),'bytes':i.bytes.hex(),'instruction':f'{i.mnemonic} {i.op_str}'} for i in actual]
checks={}
checks['recovery_header_magic_result_retained']=expect(0x41e04632,[('bl','#0x41e25cbc'),('mov','r7, r0'),('cmp','r0, #0'),('bne','#0x41e0471c')])
checks['recovery_checker_return_discarded']=expect(0x41e046d8,[('bl','#0x41e03fec'),('mov','r0, r7'),('add','sp, #0xc'),('pop.w','{r4, r5, r6, r7, r8, sb, pc}')])
checks['boot_checker_return_discarded']=expect(0x41e04450,[('bl','#0x41e03fec'),('mov','r0, r7'),('add','sp, #0xc'),('pop.w','{r4, r5, r6, r7, r8, sb, pc}')])
checks['early_policy_failure_continues']=expect(0x41e1e222,[('bl','#0x41e39650'),('cbnz','r0, #0x41e1e254'),('bl','#0x41e1de50')])
checks['early_failure_records_red']=expect(0x41e1e254,[('ldr','r3, [pc, #0xd8]'),('movs','r2, #3'),('ldr','r3, [r4, r3]'),('str','r2, [r3]'),('b','#0x41e1e228')])
checks['red_screen_returns_failure']=expect(0x41e03f3e,[('mov.w','r0, #-1'),('pop','{r3, pc}')])
# Resolve r4 setup, the global-offset-table slot, and both uses of the same state.
got=(0x41e1e15e+4+word(0x41e1e2f0))&0xffffffff
assert got==0x41e6500c
slot=got+word(0x41e1e330)
assert slot==0x41e650ac and word(slot)==0x41e68518
screen_slot=(0x41e03f58+4+word(0x41e03f8c))&0xffffffff
mode_slot=(0x41e1a90a+4+word(0x41e1a91c))&0xffffffff
assert screen_slot==slot
assert word(mode_slot)==0x41e68500 and mode_slot!=slot
assert 0x41e1de78+2*struct.unpack_from('<H',data,0x41e1de7c-base+512)[0]==0x41e1e006
checks['recovery_dispatch']={'boot_mode':2,'table_entry_address':'0x41e1de7c','target':'0x41e1e006'}
checks['state_pointer_resolution']={'got':hex(got),'early_failure_and_screen_state_slot':hex(slot),'verified_boot_state':hex(word(slot)),'boot_mode':hex(word(mode_slot)),'conclusion':'The stored 3 is verified-boot red, not boot-mode fastboot.'}
backups=[]
expected='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
for rel in ['artifacts/device-backup/initial/recovery.bin','artifacts/device-backup/verify/recovery.bin']:
 path=old/rel;b=path.read_bytes();digest=hashlib.sha256(b).hexdigest()
 assert len(b)==16740352 and digest==expected
 backups.append({'path':str(path),'bytes':len(b),'sha256':digest})
gpt=json.loads((workspace/'2026-11-05-asus-root-hardware-validation/evidence/raw-gpt-verification.json').read_text())
part=next(p for p in gpt['partitions'] if p['name']=='recovery')
assert part['start_sector']==160184 and part['sectors']==32696 and part['size_bytes']==16740352
part.update({'linux_node':'/dev/block/mmcblk0p10','offset_hex':hex(part['start_sector']*512),'length_hex':hex(part['size_bytes']),'end_exclusive_hex':hex((part['start_sector']+part['sectors'])*512)})
result={'analysis_kind':'offline static checks and local backup hashes; no device test','lk_sha256':sha,'checks':checks,'recovery_partition':part,'restoration_sources':backups,'hardware_custom_acceptance':'unproved','failed_recovery_return_and_rewrite':'not yet demonstrated'}
(root/'evidence/acceptance-facts.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: instruction sequences, red-state pointer distinct from boot mode, two recovery hashes, and saved GPT geometry. No hardware inference tested.')
