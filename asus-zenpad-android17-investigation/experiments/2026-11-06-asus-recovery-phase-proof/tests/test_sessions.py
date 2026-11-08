"""Exact included session/guards/SHA; only Darwin/Linux API and storage tracing adapters.
Regular-file RESCUE_TEST validates actual paths/geometry/aliases/CID/GPT/mounts.
No production block/SELinux/peer/exclusive-lock qualification is implied.
"""
from pathlib import Path
import hashlib,json,os,resource,socket,struct,subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]; C=1048576
H=lambda b:hashlib.sha256(b).digest()
SIZES={9:2*C+512,10:8192,25:3*C+512,26:5*C+3584,0:65536}
START={9:127488,10:160184,25:1072424,26:8404264}
def limits():
 # Darwin rejects RLIMIT_AS/DATA/RSS (EINVAL); verify actual peak RSS instead.
 if os.uname().sysname!='Darwin' and not os.environ.get('SANITIZER_CGROUP'):resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
 resource.setrlimit(resource.RLIMIT_CPU,(30,30))
 os.environ['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
def send(s,op,b=b''):s.sendall(b'RSC1'+struct.pack('<II',op,len(b))+b)
def exact(s,n):
 b=b''
 while len(b)<n:
  x=s.recv(n-len(b))
  if not x:raise EOFError()
  b+=x
 return b
def recv(s,op):
 h=exact(s,12);assert h[:4]==b'RSC1';o,n=struct.unpack('<II',h[4:]);b=exact(s,n)
 if o!=op:raise ValueError((o,b))
 return b
class Sessions(unittest.TestCase):
 baseline=False
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=R/'evidence');self.root=Path(self.tmp.name)
  self.recovery=b'R'*8192;self.original=[b'S'*SIZES[25],b'B'*SIZES[9]]
  self.install=[b'I'*SIZES[25],b'J'*SIZES[9],b'D'*SIZES[26]]
  self.data=self.original+self.install;self.manifest=b'ASUSR002'+struct.pack('<II',2,5)+H(b'0'*32)+H(bytes(17408))+H(bytes(16896))
  for role,data in enumerate(self.data):
   part=[25,9,25,9,26][role];chunks=[H(data[o:o+C]) for o in range(0,len(data),C)]
   self.manifest+=struct.pack('<IIQ',role,part,len(data))+H(data)+struct.pack('<I',len(chunks))+b''.join(chunks)
  self.write('/rescue.manifest',self.manifest);self.write('/sys/class/block/mmcblk0/device/cid',b'0'*32)
  self.write('/sys/fs/selinux/enforce',b'1\n');self.write('/proc/self/mountinfo',b'1 0 0:1 / / rw - tmpfs tmpfs rw\n')
  for part in SIZES:
   self.write('/dev/block/mmcblk0'+(f'p{part}' if part else ''),{9:self.original[1],10:self.recovery,25:self.original[0],26:bytes(SIZES[26]),0:bytes(SIZES[0])}[part])
   self.write(f'/sys/dev/block/179:{part}/dev',f'179:{part}\n'.encode());self.write(f'/sys/dev/block/179:{part}/size',str(SIZES[part]//512).encode())
   if part:self.write(f'/sys/dev/block/179:{part}/start',str(START[part]).encode())
   self.p(f'/sys/dev/block/179:{part}/holders').mkdir()
  aliases='/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name'
  self.p(aliases).mkdir(parents=True)
  for part,name in [(9,'boot'),(10,'recovery'),(25,'system'),(26,'userdata')]:self.p(aliases+'/'+name).symlink_to(self.p(f'/dev/block/mmcblk0p{part}'))
  self.p('/dev/rescue-state').mkdir();self.proc=None;self.sockets=[]
 def p(self,s):return self.root/s.lstrip('/')
 def write(self,s,b):
  p=self.p(s);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 def start(self,fault='',env=None,second=False):
  a,b=socket.socketpair();self.sockets.append(a);e=os.environ.copy();e.update(env or {});fds=[b.fileno()]
  if second:
   c,d=socket.socketpair();self.sockets.append(c);fds.append(d.fileno());e['SECOND_FD']=str(d.fileno())
  cmd=[str(R/'tests'/('session-before' if self.baseline else 'session-after')),str(self.root),str(b.fileno())]
  if fault:cmd.append(fault)
  self.proc=subprocess.Popen(cmd,pass_fds=fds,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=e,preexec_fn=limits)
  b.close()
  if second:d.close()
  a.settimeout(5)
  return a
 def finish(self):
  for s in self.sockets:
   try:s.shutdown(socket.SHUT_RDWR)
   except OSError:pass
   s.close()
  out,err=self.proc.communicate(timeout=8);self.assertEqual(self.proc.returncode,0,err.decode());self.assertEqual(err,b'')
  result=json.loads(out);self.assertEqual(result['held_recovery_fds'],0);self.assertLess(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,1024**3 if os.uname().sysname=='Darwin' else 1024**2);self.proc=None;return result
 def tearDown(self):
  for s in self.sockets:s.close()
  if self.proc:self.proc.kill();self.proc.communicate()
  self.tmp.cleanup()
 def recon(self,s,role=0,pin=None,inv=None):
  b=H(self.manifest)+(pin or H(self.recovery))+struct.pack('<I',role)
  if inv is not None:b+=struct.pack('<I',inv)+H(self.data[role])
  send(s,8 if inv is not None else 2,b);return recv(s,0x82)[:32]
 def begin(self,s,role=0):
  t=self.recon(s,role);send(s,3,t);recv(s,0x83);return t
 def chunk(self,s,role,j,skip=False):
  send(s,7 if skip else 4,b'' if skip else self.data[role][j*C:(j+1)*C]);return recv(s,0x84)
 def whole(self,s,role=0):send(s,5);self.assertEqual(recv(s,0x85),H(self.data[role]))
 def commit(self,s,role=0):send(s,9,H(self.data[role]));self.assertEqual(recv(s,0x89),H(self.data[role]))
 def complete(self,s,role=0,skip=True):
  self.begin(s,role)
  for j in range((len(self.data[role])+C-1)//C):self.chunk(s,role,j,skip)
  self.whole(s,role);self.commit(s,role)
 def rejected(self,s):
  with self.assertRaises((EOFError,ValueError,ConnectionResetError)):recv(s,0x84)
 def test_skip_counts(self):
  s=self.start();self.complete(s);r=self.finish();self.assertEqual(r['recovery_hashes'],9 if self.baseline else 5);self.assertEqual(r['recovery_opens'],9 if self.baseline else 1);self.assertEqual(r['recovery_bytes'],8192*(9 if self.baseline else 5));self.assertEqual(r['target_writes'],0);self.assertEqual(r['rc'],0)
 def test_write_counts(self):
  self.write('/dev/block/mmcblk0p25',b'X'*SIZES[25]);s=self.start();self.complete(s,skip=False);r=self.finish();self.assertEqual(r['target_writes'],4);self.assertEqual(r['recovery_hashes'],9 if self.baseline else 5)
 def test_recovery_wrong_at_reconciliation(self):
  self.write('/dev/block/mmcblk0p10',b'X'*8192);s=self.start()
  with self.assertRaises(ValueError):self.recon(s)
  self.assertEqual(self.finish()['target_writes'],0)
 def test_recovery_changed_before_activation(self):
  s=self.start();t=self.recon(s);self.write('/dev/block/mmcblk0p10',b'X'*8192);send(s,3,t);self.rejected(s);self.assertEqual(self.finish()['uncertain'],-1)
 def test_recovery_changed_before_verify(self):
  s=self.start();self.begin(s)
  for j in range(4):self.chunk(s,0,j,True)
  self.write('/dev/block/mmcblk0p10',b'X'*8192);send(s,5);self.rejected(s);self.assertEqual(self.finish()['uncertain'],0)
 def test_recovery_changed_before_commit(self):
  s=self.start();self.begin(s)
  for j in range(4):self.chunk(s,0,j,True)
  self.whole(s);self.write('/dev/block/mmcblk0p10',b'X'*8192);send(s,9,H(self.data[0]));self.rejected(s);self.assertEqual(self.finish()['uncertain'],0)
 def test_midphase_content_witness(self):
  s=self.start();self.begin(s);self.chunk(s,0,0,True);self.write('/dev/block/mmcblk0p10',b'X'*8192)
  if self.baseline:
   send(s,7);self.rejected(s)
  else:
   for j in range(1,4):self.chunk(s,0,j,True)
   send(s,5);self.rejected(s)
  r=self.finish();self.assertEqual(r['uncertain'],0);self.assertEqual(r['rc'],-1)
 def test_recovery_node_replacement(self):
  s=self.start();self.begin(s);self.p('/dev/block/mmcblk0p10').rename(self.p('/dev/block/old'));self.write('/dev/block/mmcblk0p10',self.recovery)
  send(s,7)
  if self.baseline:recv(s,0x84) # old code reopens and accepts byte-identical replacement
  else:self.rejected(s)
  self.finish()
 def test_guard_changes(self):
  mutations={
   'alias':lambda:self.p('/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery').unlink(),
   'size':lambda:self.write('/sys/dev/block/179:10/size',b'1'),
   'start':lambda:self.write('/sys/dev/block/179:10/start',b'1'),
   'cid':lambda:self.write('/sys/class/block/mmcblk0/device/cid',b'1'*32),
   'gpt':lambda:self.write('/dev/block/mmcblk0',b'X'*65536),
   'mount':lambda:self.write('/proc/self/mountinfo',b'1 0 179:10 / / rw - ext4 mmc rw\n'),
   'holder':lambda:self.write('/sys/dev/block/179:10/holders/dm',b''),
   'enforce':lambda:self.write('/sys/fs/selinux/enforce',b'0'),
  }
  for name,mutate in mutations.items():
   with self.subTest(name=name):
    # Each mutation uses a fresh fixture/process; preserve source test before teardown.
    if self.proc:self.finish()
    self.tearDown();self.setUp();s=self.start();self.begin(s);mutate();send(s,7);self.rejected(s);self.assertEqual(self.finish()['target_writes'],0)
 def test_target_node_replaced(self):
  s=self.start();self.begin(s);self.p('/dev/block/mmcblk0p25').rename(self.p('/dev/block/old'));self.write('/dev/block/mmcblk0p25',self.original[0]);send(s,7);self.rejected(s);self.finish()
 def test_recovery_open_error(self):
  s=self.start(env={'FAIL_RECOVERY_OPEN':'1'})
  with self.assertRaises(ValueError):self.recon(s)
  self.assertEqual(self.finish()['recovery_hashes'],0)
 def test_recovery_short_read(self):
  s=self.start(env={'SHORT_RECOVERY':'1'})
  with self.assertRaises(ValueError):self.recon(s)
  self.assertEqual(self.finish()['target_writes'],0)
 def test_bad_source_chunk(self):
  s=self.start();self.begin(s);send(s,4,b'X'*C);self.rejected(s);self.assertEqual(self.finish()['target_writes'],0)
 def test_false_skip(self):
  self.write('/dev/block/mmcblk0p25',b'X'*SIZES[25]);s=self.start();self.begin(s);send(s,7);self.rejected(s);self.assertEqual(self.finish()['target_writes'],0)
 def test_storage_failures(self):
  for f in ['write','flush','read','shortread','publish','ack']:
   with self.subTest(fault=f):
    self.tearDown();self.setUp();self.write('/dev/block/mmcblk0p25',b'X'*SIZES[25]);s=self.start(fault=f)
    try:
     self.begin(s);send(s,4,self.original[0][:C]);self.rejected(s)
    except (EOFError,ValueError):pass
    self.assertEqual(self.finish()['rc'],-1)
 def test_disconnect_reconcile_fresh_token_and_pin(self):
  s=self.start(second=True);old=self.begin(s);s.shutdown(socket.SHUT_RDWR);s.close();later=self.sockets[1];later.settimeout(5)
  t=self.recon(later);self.assertNotEqual(t,old);send(later,3,old);self.rejected(later);self.assertEqual(self.finish()['uncertain'],0)
 def test_changed_pin_after_uncertainty_rejected(self):
  s=self.start(second=True);self.begin(s);s.shutdown(socket.SHUT_RDWR);s.close();later=self.sockets[1]
  with self.assertRaises(ValueError):self.recon(later,pin=b'X'*32)
  self.assertEqual(self.finish()['uncertain'],0)
 def test_inverse_after_uncertainty(self):
  s=self.start(second=True);self.begin(s,2);s.shutdown(socket.SHUT_RDWR);s.close();later=self.sockets[1];t=self.recon(later,0,inv=2);send(later,3,t);recv(later,0x83)
  for j in range(4):self.chunk(later,0,j,True)
  self.whole(later);self.commit(later);self.assertEqual(self.finish()['rc'],0)
 def test_prerequisites(self):
  s=self.start()
  with self.assertRaises(ValueError):self.recon(s,3)
  self.assertEqual(self.finish()['target_writes'],0)
 def test_lost_commit_receipt(self):
  s=self.start();self.begin(s)
  for j in range(4):self.chunk(s,0,j,True)
  self.whole(s);send(s,9,H(self.data[0]));self.assertEqual(exact(s,12)[:4],b'RSC1') # deliberately do not accept payload
  self.proc.wait(timeout=8);r=self.finish();self.assertEqual(r['uncertain'],-1);self.assertEqual(r['frozen'],0) # host still UNKNOWN
 def test_after_reconciliation_scan_mutation(self):
  s=self.start(env={'MUTATE_AFTER_SCAN':'1'})
  with self.assertRaises((EOFError,ValueError)):self.recon(s)
  self.assertEqual(self.finish()['target_writes'],0)
 def test_write_readback_and_publication_failures(self):
  for env in [{'FAIL_FSYNC_AT':'3'},{'CORRUPT_READBACK':'1'},{'FAIL_RENAME_AT':'2'}]:
   with self.subTest(env=env):
    self.tearDown();self.setUp();self.write('/dev/block/mmcblk0p25',b'X'*SIZES[25]);s=self.start(env=env);self.begin(s)
    try:
     for j in range(4):self.chunk(s,0,j)
     send(s,5);self.rejected(s)
    except (EOFError,ValueError):pass
    r=self.finish();self.assertEqual(r['rc'],-1);self.assertEqual(r['uncertain'],0);self.assertGreater(r['target_writes'],0)
 def test_early_verify_and_replayed_activation(self):
  s=self.start();t=self.begin(s);send(s,3,t);self.rejected(s);self.assertEqual(self.finish()['uncertain'],0)
if __name__=='__main__':
 import sys
 if '--baseline' in sys.argv:sys.argv.remove('--baseline');Sessions.baseline=True
 unittest.main(verbosity=2)
