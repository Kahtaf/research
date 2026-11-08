import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from rescue import *
ROOT=Path(__file__).resolve().parents[1]
ZERO=bytes(CHUNK)
BOOT=(ROOT.parent/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/boot.bin').read_bytes()

def image(size,reader):
 h=hashlib.sha256();chunks=[]
 for off in range(0,size,CHUNK):
  data=reader(off,min(CHUNK,size-off));h.update(data);chunks.append(SHA(data))
 return dict(bytes=size,sha256=h.hexdigest(),chunks=chunks)
def zeros(off,n):return ZERO[:n]
def base_manifest():
 boot=image(len(BOOT),lambda o,n:BOOT[o:o+n]);assert boot['sha256']==ORIGINAL_BOOT
 system=image(PARTS['system']['sectors']*512,zeros)
 candidate=image(len(BOOT),zeros)
 m=dict(version=1,approved=True,identity=dict(serial=SERIAL,gpt_sha256=GPT,emmc_cid='1'*32),geometry=PARTS,
 recovery_sha256='2'*64,images=dict(original_boot=boot,original_system=system,candidate_boot=candidate,candidate_system=system,fresh_userdata=None,footer_magic=dict(bytes=4,sha256=SHA(bytes(4)),chunks=[SHA(bytes(4))])),
 backup_receipts={},migration=False,footer_review=False,parent_runtime_gates=dict(recovery_authenticated=True,recovery_restore_tested=True,physical_reentry_tested=True,exclusive_writer=True))
 for part,digest in [('boot',ORIGINAL_BOOT),('system',system['sha256']),('recovery',ORIGINAL_RECOVERY)]:
  m['backup_receipts'][part]=dict(bytes=PARTS[part]['sectors']*512,sha256=digest,source_read_twice=True,durable_destination_reread=True,parent_verified=True)
 return m
BASE=base_manifest()
def reviewed(m):
 raw=json.dumps(m).encode();return parse_manifest(raw,SHA(raw))

class FakeBlocks:
 """Byte-backed sparse fake with exact production geometry; no device/files opened.
 Unwritten SYSTEM bytes are zeros; BOOT bytes come from the unchanged local backup.
 """
 def __init__(self,m):
  self.m=m;self.chunks={};self.calls=[];self.bad=None;self.loss=None;self.writes=[];self.reads=0
 def identity(self):
  self.calls.append('identity');return self.m['identity'] if self.bad!='identity' else {}
 def geometry(self,p):
  self.calls.append('geometry');g=PARTS[p].copy()
  if self.bad=='geometry':g['start']+=1
  return g
 def alias_matches(self,p):self.calls.append('alias');return self.bad!='alias'
 def unmounted(self,p):self.calls.append('mount');return self.bad!='mount'
 def recovery_hash(self):self.calls.append('recovery');return '3'*64 if self.bad=='recovery' else self.m['recovery_sha256']
 def read_at(self,p,off,n):
  self.reads+=1
  if self.loss=='read':raise TransportLost('read disconnected')
  key=(p,off//CHUNK)
  if key in self.chunks:data=self.chunks[key][off%CHUNK:off%CHUNK+n]
  elif p=='boot':data=BOOT[off:off+n]
  elif p=='metadata' and off==0:data=bytes.fromhex('c4b1b5d0')+ZERO[4:n]
  else:data=ZERO[:n]
  if self.loss=='short-read':return data[:-1]
  return data
 def write_at(self,p,off,data):
  self.calls.append('write');self.writes.append((p,off,len(data)))
  if self.loss=='write':
   self.chunks[(p,off//CHUNK)]=data[:512]+self.read_at(p,off+512,len(data)-512)
   raise TransportLost('write disconnected after partial mutation')
  if len(data)==4:self.chunks[(p,0)]=data+self.read_at(p,4,CHUNK-4)
  else:self.chunks[(p,off//CHUNK)]=data
  if self.loss=='short-write':return len(data)-1
  return len(data)
 def flush(self,p):
  self.calls.append('flush')
  if self.loss=='flush':raise TransportLost('flush disconnected')
 def journal(self,event):
  self.calls.append('journal')
  if self.loss=='journal':raise TransportLost('journal unavailable')

class RescueTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=NativeGate(ROOT/'artifacts/rescue-v1/librescue_gate.dylib')
 def session(self,m=None,peer=None,execute=True):
  m=reviewed(m or copy.deepcopy(BASE));b=FakeBlocks(m);s=Session(m,self.g,b,peer or Peer(2000,'u:r:shell:s0'),execute=execute);return s,b
 def feed_boot(self,s):
  size=len(BOOT)
  for i,off in enumerate(range(0,size,CHUNK)):s.feed(i,ZERO[:min(CHUNK,size-off)])
 def test_plan_has_no_backend_calls(self):
  s,b=self.session(execute=False);self.assertEqual(s.begin('install-boot')['mode'],'PLAN_ONLY');self.assertEqual(b.calls,[])
 def test_manifest_refuses_unreviewed_missing_backup_geometry_and_unknown_fields(self):
  for change in ('approved','system','receipt','geometry','unknown','runtime','cid'):
   m=copy.deepcopy(BASE)
   if change=='approved':m['approved']=False
   elif change=='system':m['images']['original_system']=None
   elif change=='receipt':m['backup_receipts']['system']['durable_destination_reread']=False
   elif change=='geometry':m['geometry']['system']['sectors']-=1
   elif change=='unknown':m['shell']='dd'
   elif change=='runtime':m['parent_runtime_gates']['physical_reentry_tested']=False
   else:m['identity']['emmc_cid']='REVIEW_REQUIRED'
   with self.subTest(change=change),self.assertRaises((Refused,TypeError)):reviewed(m)
  with self.assertRaises(Refused):parse_manifest(json.dumps(BASE).encode(),'0'*64)
 def test_exact_native_geometry_and_fixed_bounds(self):
  for op,part,key in OPS.values():
   self.assertTrue(self.g.geometry(op,PARTS[part]))
   for field in PARTS[part]:
    bad=PARTS[part].copy();bad[field]+=1;self.assertFalse(self.g.geometry(op,bad))
  self.assertFalse(self.g.frame(999,0,512,0,2000,'u:r:shell:s0',True,True))
  for off,n,expected in [(1,512,1),(0,CHUNK+512,0),(len(BOOT),512,len(BOOT)),(0,512,512),(-1,512,-1)]:
   self.assertFalse(self.g.frame(1,off,n,expected,2000,'u:r:shell:s0',False,False))
  self.assertFalse(self.g.frame(6,0,512,0,2000,'u:r:shell:s0',True,True))
  self.assertFalse(self.g.frame(5,0,512,0,2000,'u:r:shell:s0',False,False))
 def test_wrong_peer_before_io(self):
  for peer in (Peer(0,'u:r:recovery:s0'),Peer(2000,'u:r:adbd:s0'),Peer(1000,'u:r:shell:s0')):
   s,b=self.session(peer=peer)
   with self.assertRaises(Refused):s.begin('restore-boot')
   self.assertEqual(b.calls,[])
 def test_identity_alias_mount_recovery_geometry_refuse_without_write(self):
  for bad in ('identity','geometry','alias','mount','recovery'):
   s,b=self.session();b.bad=bad
   with self.assertRaises(Refused):s.begin('install-boot',system_verified=True,data_verified=True)
   self.assertFalse(b.writes)
 def test_boot_last(self):
  s,b=self.session()
  with self.assertRaises(Refused):s.begin('install-boot')
  self.assertFalse(b.calls)
 def test_original_restore_no_redundant_write(self):
  s,b=self.session();self.assertEqual(s.begin('restore-boot'),'already-original');self.assertEqual(s.state,State.DONE);self.assertFalse(b.writes)
 def test_install_full_readback(self):
  s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True);self.feed_boot(s)
  self.assertEqual(s.finish(),State.DONE.value);self.assertEqual(sum(x[2] for x in b.writes),len(BOOT));self.assertEqual({x[0] for x in b.writes},{'boot'})
  with self.assertRaises(Refused):s.feed(0,ZERO)
 def test_restore_fixed_original_after_changed_partition(self):
  s,b=self.session();b.chunks[('boot',0)]=ZERO;s.begin('restore-boot')
  for i,off in enumerate(range(0,len(BOOT),CHUNK)):s.feed(i,BOOT[off:off+CHUNK])
  self.assertEqual(s.finish(),State.DONE.value)
 def test_bad_chunk_and_sequence_before_write(self):
  for idx,data in [(0,b'X'*CHUNK),(1,ZERO),(0,b'X')]:
   s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True)
   with self.assertRaises(Refused):s.feed(idx,data)
   self.assertFalse(b.writes);self.assertEqual(s.state,State.FAILED)
 def test_loss_no_inverse_no_retry_no_cleanup(self):
  for loss in ('write','short-write','journal'):
   s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True);b.loss=loss
   with self.assertRaises(TransportLost):s.feed(0,ZERO)
   self.assertEqual(s.state,State.UNCERTAIN);count=len(b.calls)
   for f in (lambda:s.feed(0,ZERO),s.finish,lambda:s.begin('restore-boot')):
    with self.assertRaises(Refused):f()
   self.assertEqual(len(b.calls),count);self.assertLessEqual(len(b.writes),1)
 def test_flush_loss_and_mismatched_readback(self):
  for loss in ('flush','corrupt'):
   s,b=self.session();s.begin('install-boot',system_verified=True,data_verified=True);self.feed_boot(s)
   if loss=='corrupt':b.chunks[('boot',0)]=b'X'*CHUNK
   else:b.loss=loss
   with self.assertRaises((TransportLost,Refused)):s.finish()
   self.assertEqual(s.state,State.UNCERTAIN if loss=='flush' else State.FAILED)
 def test_readback_stream_and_sink_loss(self):
  s,b=self.session();h=hashlib.sha256()
  result=s.readback('boot',lambda off,data,sha:h.update(data));self.assertEqual(result['sha256'],ORIGINAL_BOOT);self.assertEqual(h.hexdigest(),ORIGINAL_BOOT);self.assertFalse(result['durable_destination_verified'])
  s,b=self.session()
  def broken(*args):raise TransportLost('sink disconnected')
  with self.assertRaises(TransportLost):s.readback('boot',broken)
  self.assertEqual(s.state,State.UNCERTAIN);self.assertFalse(b.writes)
 def test_full_system_geometry_sparse_readback(self):
  s,b=self.session();result=s.readback('system',lambda *args:None)
  self.assertEqual(result['bytes'],3753902080);self.assertEqual(result['sha256'],BASE['images']['original_system']['sha256'])
 def test_full_system_restore_only_p25(self):
  s,b=self.session();b.chunks[('system',0)]=b'X'*CHUNK;s.begin('restore-system');size=3753902080
  for i,off in enumerate(range(0,size,CHUNK)):s.feed(i,ZERO[:min(CHUNK,size-off)])
  self.assertEqual(s.finish(),State.DONE.value)
  self.assertEqual(sum(x[2] for x in b.writes),size);self.assertEqual({x[0] for x in b.writes},{'system'})
 def test_footer_four_bytes_only_preserves_rest(self):
  m=copy.deepcopy(BASE);m['migration']=m['footer_review']=True
  metadata=image(PARTS['metadata']['sectors']*512,lambda off,n:bytes.fromhex('c4b1b5d0')+ZERO[4:n] if off==0 else ZERO[:n])
  m['backup_receipts']['metadata']=dict(sha256=metadata['sha256'],bytes=33554432,source_read_twice=True,parent_verified=True)
  s,b=self.session(m);s.begin('invalidate-footer-magic');s.feed(0,bytes(4));self.assertEqual(s.finish(),State.DONE.value);self.assertEqual(b.writes,[('metadata',0,4)])
 def test_full_p26_provision_fake_bytes_exact_bounds(self):
  m=copy.deepcopy(BASE);m['migration']=True
  m['images']['fresh_userdata']=image(PARTS['userdata']['sectors']*512,zeros)
  s,b=self.session(m);s.begin('provision-data');size=PARTS['userdata']['sectors']*512
  for i,off in enumerate(range(0,size,CHUNK)):s.feed(i,ZERO[:min(CHUNK,size-off)])
  self.assertEqual(s.finish(),State.DONE.value)
  self.assertEqual(sum(x[2] for x in b.writes),11331268096)
  self.assertEqual({x[0] for x in b.writes},{'userdata'})
  self.assertEqual(b.writes[-1][1]+b.writes[-1][2],11331268096)
 def test_footer_and_userdata_require_separate_review(self):
  for op in ('invalidate-footer-magic','provision-data'):
   s,b=self.session()
   with self.assertRaises(Refused):s.begin(op)
   self.assertFalse(b.calls)
 def test_recovery_and_security_writes_have_no_operation(self):
  for op in ('restore-recovery','write-gpt','wipe-metadata','format','shell','write-lk','write-para'):
   s,b=self.session()
   with self.assertRaises(Refused):s.begin(op)
   self.assertFalse(b.calls)
if __name__=='__main__':unittest.main(verbosity=2)
