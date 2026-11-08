#!/usr/bin/env python3
"""Create a NEW unapproved contract, never approve or upload anything."""
from pathlib import Path
import argparse,json,hashlib
from rescue import PARTS,SERIAL,GPT,CHUNK,ORIGINAL_BOOT,ORIGINAL_RECOVERY
ROOT=Path(__file__).resolve().parents[1]
def describe(path,size):
 if not path.is_file() or path.is_symlink() or path.stat().st_size!=size:raise ValueError('regular exact-size image required')
 h=hashlib.sha256();chunks=[]
 with path.open('rb') as f:
  while data:=f.read(CHUNK):h.update(data);chunks.append(hashlib.sha256(data).hexdigest())
 return dict(bytes=size,sha256=h.hexdigest(),chunks=chunks)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 boot=describe(ROOT.parent/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/boot.bin',16740352)
 assert boot['sha256']==ORIGINAL_BOOT
 m=dict(version=1,approved=False,identity=dict(serial=SERIAL,gpt_sha256=GPT,emmc_cid=None),geometry=PARTS,recovery_sha256=None,
  images=dict(original_boot=boot,original_system=None,candidate_boot=None,candidate_system=None,fresh_userdata=None,
   footer_magic=dict(bytes=4,sha256=hashlib.sha256(bytes(4)).hexdigest(),chunks=[hashlib.sha256(bytes(4)).hexdigest()])),
  backup_receipts={p:dict(bytes=PARTS[p]['sectors']*512,sha256=h,source_read_twice=False,durable_destination_reread=False,parent_verified=False) for p,h in [('boot',ORIGINAL_BOOT),('system',None),('recovery',ORIGINAL_RECOVERY)]},
  migration=False,footer_review=False,parent_runtime_gates=dict(recovery_authenticated=False,recovery_restore_tested=False,physical_reentry_tested=False,exclusive_writer=False))
 with a.out.open('x') as f:json.dump(m,f,indent=2)
if __name__=='__main__':main()
