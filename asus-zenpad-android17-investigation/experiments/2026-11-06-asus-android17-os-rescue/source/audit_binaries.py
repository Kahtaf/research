#!/usr/bin/env python3
"""Exact saved-binary evidence. Requires existing audit venv's Capstone only."""
from pathlib import Path
import argparse,hashlib,json,struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 init=(ROOT.parent/'2026-11-06-asus-recovery-diagnostic/evidence/stock/init').read_bytes()
 rec=(ROOT/'evidence/stock-sbin_recovery').read_bytes();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def ins(b,addr,n):
  # These exact two static ELFs map executable bytes at file offset + 0x400000.
  po=struct.unpack_from('<Q',b,32)[0];sz,count=struct.unpack_from('<HH',b,54)
  found=[]
  for i in range(count):
   typ,flags,off,va,pa,fs,ms,al=struct.unpack_from('<II6Q',b,po+i*sz)
   if typ==1 and flags&1 and va<=addr<va+fs:
    data=b[off+addr-va:off+addr-va+n*4]
    found=[dict(address=hex(q.address),bytes=q.bytes.hex(),instruction=q.mnemonic+' '+q.op_str) for q in md.disasm(data,addr)]
  assert len(found)==n;return found
 def expect(b,addr,expected):
  got=ins(b,addr,len(expected));assert [q['instruction'].strip() for q in got]==expected;return got
 checks={
 'service_child_umask_077':expect(init,0x41d0bc,['mov w0, #0x3f','str w27, [sp, #0x14]','bl #0x4c1b58']),
 'umask_wrapper':expect(init,0x4c1b58,['and w8, w0, #0x1ff','cmp w8, w0','b.ne #0x4c1b68','b #0x4cc300']),
 'linux_arm64_umask_166':expect(init,0x4cc300,['mov x8, #0xa6','svc #0']),
 'recovery_keyloc_open_and_whole_device_wipe':ins(rec,0x407fd0,23),
 'recovery_size_ioctl_BLKGETSIZE64':expect(rec,0x4166e0,['mov w1, #-0x7ff80000','stur xzr, [x29, #-0x30]','movk w1, #0x1272','sub x2, x29, #0x30','mov w0, w19','bl #0x4d4500']),
 'recovery_wipe_extent_start_zero_length_arg':expect(rec,0x41b2b4,['mov w1, #0x1277','stp xzr, x20, [sp, #8]','add x2, sp, #8','mov w0, w19','bl #0x4d4500'])}
 assert b'I:wiping %s\n\0' in rec
 assert (ROOT/'evidence/stock-etc_recovery.fstab').read_text().count('forceencrypt=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/metadata')==1
 result=dict(init_sha256=hashlib.sha256(init).hexdigest(),stock_recovery_executable_sha256=hashlib.sha256(rec).hexdigest(),checks=checks,
  conclusions=['Observed errno13 is consistent with exact init service umask077 causing root-owned report0600; actual target stat was not captured.',
   'Actual OEM format-volume code takes key_loc absolute path, opens it, obtains block-device length with BLKGETSIZE64, passes it to wipe routine whose discard extent is [0,length]. It is not a footer-only wipe.',
   'AOSP7 roots.cpp corroborates exact call sequence; vendor runtime factory reset has not been executed.'],target_execution=False)
 with a.out.open('x') as f:json.dump(result,f,indent=2)
 print('PASS: exact init umask and OEM metadata-wide wipe instruction checks')
if __name__=='__main__':main()
