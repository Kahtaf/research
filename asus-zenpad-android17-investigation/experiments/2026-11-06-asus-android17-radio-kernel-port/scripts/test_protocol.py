#!/usr/bin/env python3
import pathlib,subprocess,tempfile,shutil,json
r=pathlib.Path(__file__).resolve().parents[1]
src=r/'staged/device/asus/p00a/radio'
out=r/'evidence/host';out.mkdir(parents=True,exist_ok=True)
binary=out/'protocol-test'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined','-I'+str(src/'src'),str(src/'src/wmt_protocol.c'),str(src/'tests/protocol_test.c'),'-o',str(binary)],check=True)
results=[]
with tempfile.TemporaryDirectory(dir=out) as tmp:
 d=pathlib.Path(tmp)
 def write(name,seq=1,count=2,fw=0x8a00,size=40):
  b=bytearray(40);b[22]=fw>>8;b[23]=fw&255;b[24]=(count<<4)|seq;b[25:28]=b'\x00\x0e\xf0';(d/name).write_bytes(b[:size])
 def run(label,bad):
  p=subprocess.run([str(binary),str(d),str(int(bad))],capture_output=True,text=True);assert p.returncode==0,(label,p.stdout,p.stderr);results.append({'case':label,'pass':True})
 def reset():
  for p in d.iterdir():p.unlink()
 run('missing patches',True)
 write('ROMv2_lm_patch_b.bin',2);run('missing sequence',True)
 write('ROMv2_lm_patch_a.bin',1);run('complete reversed filenames, real ioctl failures',False)
 write('ROMv2_lm_patch_duplicate.bin',1);run('duplicate sequence',True);reset()
 write('ROMv2_lm_patch_a.bin',0);run('zero sequence',True);reset()
 write('ROMv2_lm_patch_a.bin',3);run('sequence exceeds count',True);reset()
 write('ROMv2_lm_patch_a.bin',1,count=0);run('zero count',True);reset()
 write('ROMv2_lm_patch_a.bin',1,count=11);run('excess count',True);reset()
 write('ROMv2_lm_patch_a.bin',1);write('ROMv2_lm_patch_b.bin',2,count=3);run('inconsistent total',True);reset()
 write('ROMv2_lm_patch_a.bin',1,fw=0x8a01);run('ROM mismatch',True);reset()
 write('ROMv2_lm_patch_a.bin',1,size=25);run('short header',True);reset()
 write('data',1);(d/'ROMv2_lm_patch_link.bin').symlink_to(d/'data');run('symlink rejected',True);reset()
 fw=r/'sourceinputs/firmware'
 for p in fw.glob('*hdr.bin'):shutil.copyfile(p,d/p.name)
 run('actual ASUS generic firmware: seq1=_1_1, seq2=_1_0',False)
(r/'evidence/protocol-tests.json').write_text(json.dumps({'compiler':'host cc ASan+UBSan','cases':results},indent=2)+'\n')
print(f'{len(results)} protocol scenarios passed (including publication fault injection).')
