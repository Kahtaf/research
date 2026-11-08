from pathlib import Path
import sys,subprocess,os,socket,struct,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests'));sys.path.insert(0,str(R/'source'))
from test_adapters import Adapter
import client
rows=[]
for case in ['idle','zero_records','four_records','five_records','bad_system','bad_boot','reconciled','writing','verified','uncertain_disconnect','dup_fail']:
 a=Adapter();a.setUp()
 try:
  if case=='five_records':a.enable_userdata()
  if case=='zero_records':a.manifest=a.manifest[:12]+bytes(4)+a.manifest[16:112]
  elif case not in ['four_records','five_records']:
   # Preserve exact first two fixture records; small regular-file geometry only.
   m=a.manifest;off=112
   for _ in range(2):count=struct.unpack_from('<I',m,off+48)[0];off+=52+count*32
   a.manifest=m[:12]+struct.pack('<I',2)+m[16:off]
  (a.root/'rescue.manifest').write_bytes(a.manifest)
  if case in ['bad_system','bad_boot']:
   part=25 if case=='bad_system' else 9;p=a.root/f'dev/block/mmcblk0p{part}';data=bytearray(p.read_bytes());data[0]^=1;p.write_bytes(data)
  p=subprocess.Popen([str(R/'artifacts/review-handoff-server-r2'),str(a.root),case],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);a.proc=p
  assert p.stdout.readline().startswith('READY')
  s=a.connect()
  if case=='reconciled':a.recon(s,0)
  if case in ['writing','verified','uncertain_disconnect']:
   same=a.begin(s,0)
   if case=='verified':
    for _ in same:client.send(s.fileno(),7);client.receive(s.fileno(),0x84)
    client.send(s.fileno(),5);client.receive(s.fileno(),0x85)
   if case=='uncertain_disconnect':s.close();s=a.connect()
  client.send(s.fileno(),0x30)
  if case=='idle':
   result=client.receive(s.fileno(),0xbe);assert result.startswith(b'HANDOFF_DESCRIPTORS_AND_EXCLUSIVE_LOCK_OK');assert p.wait(timeout=5)==0
  else:
   try:client.receive(s.fileno(),0xbe);raise AssertionError('handoff accepted')
   except (EOFError,RuntimeError,ConnectionError):pass
   if case=='dup_fail':assert p.wait(timeout=5)==74
  s.close();rows.append(dict(case=case,passed=True,handoff_reached=(case=='idle'),fixture_geometry='small regular files',real_exec_and_SELinux_transition_tested=False))
 finally:a.tearDown()
(R/'evidence/handoff-review.json').write_text(json.dumps(rows,indent=2)+'\n');print('HANDOFF_REVIEW_PASS',len(rows))
