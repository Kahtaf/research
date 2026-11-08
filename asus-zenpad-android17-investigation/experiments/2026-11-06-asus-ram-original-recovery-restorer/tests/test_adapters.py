import hashlib,json,os,socket,struct,subprocess,tempfile,time,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
import client
R=Path(__file__).resolve().parents[1];C=1048576
def h(b):return hashlib.sha256(b).digest()
class Adapter(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=R/'artifacts',prefix='fixture-');self.root=Path(self.tmp.name);self.proc=None
  self.original=[b'S'*(3*C+512),b'B'*(2*C+512)]
  self.install=[b'T'*(3*C+512),b'C'*(2*C+512)]
  self.raw=self.original+self.install
  self.recovery=b'R'*8192;disk=b'G'*65536;self.cid='0'*32
  def put(p,b):
   f=self.root/p.lstrip('/');f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
  put('/dev/block/mmcblk0',disk);put('/dev/block/mmcblk0p10',self.recovery)
  put('/dev/block/mmcblk0p25',self.original[0]);put('/dev/block/mmcblk0p9',self.original[1])
  put('/sys/fs/selinux/enforce',b'1\n');put('/sys/class/block/mmcblk0/device/cid',self.cid.encode()+b'\n');put('/proc/self/mountinfo',b'')
  for part,name,start,size in [(0,None,0,65536),(9,'boot',127488,len(self.original[1])),(10,'recovery',160184,8192),(25,'system',1072424,len(self.original[0]))]:
   base='/sys/dev/block/179:'+str(part)
   put(base+'/dev',f'179:{part}\n'.encode());put(base+'/size',str(size//512).encode());put(base+'/start',str(start).encode());(self.root/(base+'/holders').lstrip('/')).mkdir()
   if name:
    alias=self.root/'dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name'/name;alias.parent.mkdir(parents=True,exist_ok=True);alias.symlink_to(self.root/f'dev/block/mmcblk0p{part}')
  (self.root/'dev/rescue-state').mkdir()
  b=b'ASUSR002'+struct.pack('<II',2,4)+h(self.cid.encode())+h(disk[:17408])+h(disk[-16896:])
  for i,data in enumerate(self.raw):
   chunks=[h(data[j:j+C]) for j in range(0,len(data),C)]
   b+=struct.pack('<IIQ',i,9 if i%2 else 25,len(data))+h(data)+struct.pack('<I',len(chunks))+b''.join(chunks)
  self.manifest=b;put('/rescue.manifest',b)
 def enable_userdata(self):
  data=b'EXT4TEST'+bytes(5*C+3584-8);self.raw.append(data)
  p=self.root/'dev/block/mmcblk0p26';p.write_bytes(b'D'*len(data))
  base=self.root/'sys/dev/block/179:26';base.mkdir()
  (base/'dev').write_text('179:26');(base/'start').write_text('8404264');(base/'size').write_text(str(len(data)//512));(base/'holders').mkdir()
  (self.root/'dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/userdata').symlink_to(p)
  chunks=[h(data[j:j+C]) for j in range(0,len(data),C)]
  self.manifest=self.manifest[:12]+struct.pack('<I',5)+self.manifest[16:]+struct.pack('<IIQ',4,26,len(data))+h(data)+struct.pack('<I',len(chunks))+b''.join(chunks)
  (self.root/'rescue.manifest').write_bytes(self.manifest)
 def start(self,fault='none'):
  self.proc=subprocess.Popen([os.environ.get('RESCUE_TEST_SERVER',str(R/'artifacts/test_server')),str(self.root),fault],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  self.assertTrue(self.proc.stdout.readline().startswith('READY'))
 def connect(self):
  s=socket.socket(socket.AF_UNIX);s.settimeout(4);s.connect(str(self.root/'server.sock'));s.setblocking(True);return s
 def tearDown(self):
  if self.proc:
   self.proc.terminate();self.proc.communicate(timeout=5)
  self.tmp.cleanup()
 def recon(self,s,index=2):
  return client.reconcile(s.fileno(),self.manifest,h(self.recovery),index)
 def begin(self,s,index=2):
  token,same,row=self.recon(s,index);client.send(s.fileno(),3,token);self.assertEqual(client.receive(s.fileno(),0x83),b'');return same
 def chunk(self,s,data):
  client.send(s.fileno(),4,data);return struct.unpack('<II',client.receive(s.fileno(),0x84))
 def complete(self,s,index=2):
  same=self.begin(s,index);raw=self.raw[index]
  for i in range(len(same)):
   if same[i]:client.send(s.fileno(),7);ack=client.receive(s.fileno(),0x84)
   else:self.chunk(s,raw[i*C:(i+1)*C])
  client.send(s.fileno(),5);self.assertEqual(client.receive(s.fileno(),0x85),h(raw));client.send(s.fileno(),9,h(raw));self.assertEqual(client.receive(s.fileno(),0x89),h(raw))
 def test_write_full_then_boot_last(self):
  self.start()
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s,3)
  with self.connect() as s:self.complete(s,2)
  self.assertEqual((self.root/'dev/block/mmcblk0p25').read_bytes(),self.install[0])
  with self.connect() as s:self.complete(s,3)
  self.assertEqual((self.root/'dev/block/mmcblk0p9').read_bytes(),self.install[1])
  with self.connect() as s:self.complete(s,0)
  with self.connect() as s:self.complete(s,1)
  self.assertEqual((self.root/'dev/block/mmcblk0p10').read_bytes(),self.recovery)
 def test_skip_and_full_readback(self):
  self.start()
  with self.connect() as s:
   same=self.begin(s,0);self.assertTrue(all(same))
   for i in range(len(same)):
    client.send(s.fileno(),7);self.assertEqual(struct.unpack('<II',client.receive(s.fileno(),0x84)),(i,1))
   client.send(s.fileno(),5);self.assertEqual(client.receive(s.fileno(),0x85),h(self.original[0]));client.send(s.fileno(),9,h(self.original[0]));self.assertEqual(client.receive(s.fileno(),0x89),h(self.original[0]))
 def test_disconnect_reconcile_actual_hashes(self):
  self.start()
  with self.connect() as s:
   self.begin(s);self.chunk(s,self.install[0][:C])
  with self.connect() as s:
   self.assertIn('FROZEN',client.status(s.fileno()));token,same,row=self.recon(s);self.assertEqual(list(same),[1,0,0,0])
  # Reconciliation token cannot be used on another connection.
  with self.connect() as s:
   client.send(s.fileno(),3,token);self.assertRaises(RuntimeError,client.receive,s.fileno(),0x83)
  with self.connect() as s:self.complete(s)
 def test_busy_writer_idle_proof_waits_for_timeout(self):
  self.start();old=self.connect();self.begin(old)
  new=self.connect();new.settimeout(.2);client.send(new.fileno(),1)
  with self.assertRaises(socket.timeout):new.recv(12)
  old.close();new.setblocking(True);self.assertIn(b'writer=idle',client.receive(new.fileno(),0x81));new.close()
 def test_corrupt_chunk_no_write(self):
  self.start()
  before=(self.root/'dev/block/mmcblk0p25').read_bytes()
  with self.connect() as s:
   self.begin(s);client.send(s.fileno(),4,b'X'*C);self.assertRaises(RuntimeError,client.receive,s.fileno(),0x84)
  self.assertEqual(before,(self.root/'dev/block/mmcblk0p25').read_bytes())
 def test_false_skip_refused(self):
  self.start()
  with self.connect() as s:
   self.begin(s);client.send(s.fileno(),7);self.assertRaises(EOFError,client.receive,s.fileno(),0x84)
 def test_faults_freeze(self):
  # Separate real process per injected syscall boundary. No fake block engine.
  for fail in ['write','flush','publish','ack','read','shortread']:
   with self.subTest(fail=fail):
    if self.proc:self.proc.terminate();self.proc.communicate();self.proc=None;(self.root/'server.sock').unlink()
    for p in ['journal','journal.new']:
     (self.root/'dev/rescue-state'/p).unlink(missing_ok=True)
    (self.root/'dev/block/mmcblk0p25').write_bytes(self.original[0]);self.start(fail)
    with self.connect() as s:
     try:self.begin(s);self.chunk(s,self.install[0][:C]);self.fail('fault accepted')
     except (EOFError,RuntimeError):pass
    with self.connect() as s:self.assertIn('FROZEN',client.status(s.fileno()))
 def test_mount_holder_alias_node_bounds(self):
  self.start()
  checks=[
   ('proc/self/mountinfo',b'12 1 179:25 / /system ro - ext4 /dev/block/mmcblk0p25 ro\n'),
   ('sys/dev/block/179:25/size',b'1'),
   ('sys/dev/block/179:25/dev',b'179:9'),
   ('sys/dev/block/179:25/start',b'1'),
   ('sys/class/block/mmcblk0/device/cid',b'1'*32),
   ('sys/fs/selinux/enforce',b'0')]
  for name,data in checks:
   with self.subTest(name=name):
    p=self.root/name;old=p.read_bytes();p.write_bytes(data)
    with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
    p.write_bytes(old)
  holder=self.root/'sys/dev/block/179:25/holders/dm-0';holder.touch()
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
  holder.unlink()
  alias=self.root/'dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/system';alias.unlink();alias.symlink_to(self.root/'dev/block/mmcblk0p9')
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
 def test_fd_no_follow_and_actual_length(self):
  self.start();p=self.root/'dev/block/mmcblk0p25';p.rename(p.with_suffix('.real'));p.symlink_to(p.with_suffix('.real'))
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
  p.unlink();p.with_suffix('.real').rename(p);p.write_bytes(b'x')
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
 def test_recovery_gpt_and_manifest_pin(self):
  self.start()
  for name in ['dev/block/mmcblk0p10','dev/block/mmcblk0']:
   p=self.root/name;old=p.read_bytes();p.write_bytes(b'x'+old[1:])
   with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
   p.write_bytes(old)
  with self.connect() as s:
   client.send(s.fileno(),2,b'X'*32+h(self.recovery)+struct.pack('<I',2));self.assertRaises(RuntimeError,client.receive,s.fileno(),0x82)
 def test_full_readback_detects_changed_earlier_chunk(self):
  self.start()
  with self.connect() as s:
   self.begin(s)
   for i in range(4):self.chunk(s,self.install[0][i*C:(i+1)*C])
   p=self.root/'dev/block/mmcblk0p25'
   with p.open('r+b') as f:f.write(b'Q')
   client.send(s.fileno(),5);self.assertRaises(EOFError,client.receive,s.fileno(),0x85)
 def test_binary_framing_fragmented_and_bounds(self):
  self.start()
  with self.connect() as s:
   msg=b'RSC1'+struct.pack('<II',1,0)
   for b in msg:s.send(bytes([b]))
   self.assertIn(b'protocol=1',client.receive(s.fileno(),0x81))
  with self.connect() as s:
   s.sendall(b'RSC1'+struct.pack('<II',4,C+1));self.assertRaises(EOFError,client.receive,s.fileno(),0x84)
  with self.connect() as s:
   client.send(s.fileno(),99);self.assertRaises(RuntimeError,client.receive,s.fileno(),0x81)
 def test_readback_fixed_chunk(self):
  self.start()
  with self.connect() as s:
   client.send(s.fileno(),6,struct.pack('<II',25,3));digest=client.receive(s.fileno(),0x86);data=client.receive(s.fileno(),0x87);self.assertEqual(len(data),512);self.assertEqual(digest,h(data))
   client.send(s.fileno(),6,struct.pack('<II',20,0));self.assertRaises(RuntimeError,client.receive,s.fileno(),0x86)
 def test_same_image_after_uncertain(self):
  self.start()
  with self.connect() as s:self.begin(s)
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s,0)
  with self.connect() as s:self.complete(s,2)
 def test_explicit_original_inverse_after_uncertain_install(self):
  self.start()
  with self.connect() as s:self.begin(s);self.chunk(s,self.install[0][:C])
  with self.connect() as s:
   token,same,row=client.reconcile(s.fileno(),self.manifest,h(self.recovery),0,inverse_from=2)
   client.send(s.fileno(),3,token);client.receive(s.fileno(),0x83)
   for i,match in enumerate(same):
    if match:client.send(s.fileno(),7);client.receive(s.fileno(),0x84)
    else:self.chunk(s,self.original[0][i*C:(i+1)*C])
   client.send(s.fileno(),5);self.assertEqual(client.receive(s.fileno(),0x85),h(self.original[0]));client.send(s.fileno(),9,h(self.original[0]));self.assertEqual(client.receive(s.fileno(),0x89),h(self.original[0]))
 def test_resume_rejects_changed_p10_pin_even_if_actual_matches(self):
  self.start()
  with self.connect() as s:self.begin(s)
  changed=b'Q'+self.recovery[1:];(self.root/'dev/block/mmcblk0p10').write_bytes(changed)
  with self.connect() as s:self.assertRaises(RuntimeError,client.reconcile,s.fileno(),self.manifest,h(changed),2)
 def test_bad_manifest_refused_at_start(self):
  cases=[self.manifest+b'X',self.manifest[:8]+struct.pack('<I',1)+self.manifest[12:],self.manifest[:116]+struct.pack('<I',10)+self.manifest[120:],self.manifest[:120]+bytes(8)+self.manifest[128:],b'X'*(1024*1024+1)]
  for b in cases:
   (self.root/'rescue.manifest').write_bytes(b)
   p=subprocess.run([os.environ.get('RESCUE_TEST_SERVER',str(R/'artifacts/test_server')),str(self.root),'none'],capture_output=True,timeout=5)
   self.assertEqual(p.returncode,3,p.stderr.decode())
 def test_optional_userdata_system_then_data_then_boot_and_zero_tail(self):
  self.enable_userdata();self.start()
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s,4)
  with self.connect() as s:self.complete(s,2)
  with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s,3)
  with self.connect() as s:self.begin(s,4);self.chunk(s,self.raw[4][:C])
  with self.connect() as s:
   _,same,row=self.recon(s,4);self.assertEqual(list(same),[1,0,0,0,0,0])
  with self.connect() as s:self.complete(s,4)
  actual=(self.root/'dev/block/mmcblk0p26').read_bytes()
  self.assertEqual(actual,self.raw[4]);self.assertEqual(actual[-3584:],bytes(3584))
  with self.connect() as s:self.complete(s,3)
 def test_userdata_readback_disabled_in_default_manifest(self):
  self.start()
  with self.connect() as s:
   client.send(s.fileno(),6,struct.pack('<II',26,0));self.assertRaises(RuntimeError,client.receive,s.fileno(),0x86)
 def test_lost_final_readback_receipt_requires_same_image_reconciliation(self):
  self.start()
  with self.connect() as s:
   self.begin(s)
   for i in range(4):self.chunk(s,self.install[0][i*C:(i+1)*C])
   client.send(s.fileno(),5);self.assertEqual(client.receive(s.fileno(),0x85),h(self.install[0]))
   # Deliberately lose final confirmation: no opcode 9.
  with self.connect() as s:
   self.assertIn('FROZEN',client.status(s.fileno()));self.assertRaises(RuntimeError,self.recon,s,3)
  with self.connect() as s:self.complete(s,2)
  with self.connect() as s:self.complete(s,3)
 def test_partial_payload_disconnect_never_writes(self):
  self.start();before=(self.root/'dev/block/mmcblk0p25').read_bytes()
  with self.connect() as s:
   self.begin(s);s.sendall(b'RSC1'+struct.pack('<II',4,C)+self.install[0][:C//2])
  with self.connect() as s:
   _,same,row=self.recon(s);self.assertEqual(list(same),[0,0,0,0])
  self.assertEqual((self.root/'dev/block/mmcblk0p25').read_bytes(),before)
 def test_write_disabled_manifest_serves_status_and_refuses_mutations(self):
  self.manifest=self.manifest[:12]+struct.pack('<I',0)+self.manifest[16:112]
  (self.root/'rescue.manifest').write_bytes(self.manifest);self.start()
  with self.connect() as s:
   self.assertIn('armed=0',client.status(s.fileno()))
   client.send(s.fileno(),2,h(self.manifest)+h(self.recovery)+struct.pack('<I',0))
   self.assertRaises(RuntimeError,client.receive,s.fileno(),0x82)
  with self.connect() as s:
   client.send(s.fileno(),6,struct.pack('<II',25,0))
   self.assertRaises(RuntimeError,client.receive,s.fileno(),0x86)
 def test_cid_sha256_exact_encoding_and_legacy_format_rejected(self):
  self.assertEqual(self.manifest[16:48],h(self.cid.encode()))
  self.start();p=self.root/'sys/class/block/mmcblk0/device/cid'
  for value in [b'G'*32,b'A'*32,b'0'*31,b'0'*33]:
   p.write_bytes(value)
   with self.connect() as s:self.assertRaises(RuntimeError,self.recon,s)
  legacy=b'ASUSR001'+struct.pack('<I',1)+self.manifest[12:16]+self.cid.encode()+self.manifest[48:]
  (self.root/'rescue.manifest').write_bytes(legacy)
  q=subprocess.run([os.environ.get('RESCUE_TEST_SERVER',str(R/'artifacts/test_server')),str(self.root),'none'],capture_output=True,timeout=5)
  self.assertEqual(q.returncode,3)
 def test_target_has_no_test_root_or_regular_backend(self):
  b=Path(os.environ.get('RESCUE_DAEMON',str(R/'artifacts/os-rescue'))).read_bytes();self.assertNotIn(b'READY uid=',b);self.assertNotIn(b'fixture-',b)
if __name__=='__main__':unittest.main(verbosity=2)
