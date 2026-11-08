#!/usr/bin/env python3
"""Offline reference controller for an authenticated recovery-side fixed transport.
No device/ADB/subprocess/network adapter exists in this module. Backends must be
explicitly supplied; the only supplied backend is a regular-file test fixture.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import argparse,ctypes,hashlib,json,re

SPIKE=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
CHUNK=1024*1024
SERIAL='DEVICE_SERIAL_REDACTED'
GPT='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae'
ORIGINAL_BOOT='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
ORIGINAL_RECOVERY='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
PARTS={
 'boot':dict(start=127488,sectors=32696,partition=9,major=179,minor=9,logical_sector=512),
 'system':dict(start=1072424,sectors=7331840,partition=25,major=179,minor=25,logical_sector=512),
 'recovery':dict(start=160184,sectors=32696,partition=10,major=179,minor=10,logical_sector=512),
 'userdata':dict(start=8404264,sectors=22131383,partition=26,major=179,minor=26,logical_sector=512),
 'metadata':dict(start=294184,sectors=65536,partition=20,major=179,minor=20,logical_sector=512)}
OPS={'restore-boot':(1,'boot','original_boot'),'restore-system':(2,'system','original_system'),
 'install-system':(3,'system','candidate_system'),'install-boot':(4,'boot','candidate_boot'),
 'provision-data':(5,'userdata','fresh_userdata'),'invalidate-footer-magic':(6,'metadata','footer_magic')}
READOPS={'boot':7,'system':8,'recovery':9,'userdata':10,'metadata':11}

class Refused(Exception):pass
class TransportLost(Exception):pass
class State(Enum):
 PLAN='PLAN_ONLY';ARMED='ARMED';WRITING='WRITING';VERIFYING='VERIFYING';DONE='FULL_READBACK_VERIFIED';UNCERTAIN='UNCERTAIN_NO_RETRY';FAILED='FAILED_STOP'

def require(ok,why):
 if not ok:raise Refused(why)
def digest_ok(h):return isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h) and h!='0'*64

class ReviewedManifest(dict):
 pass

def parse_manifest(raw,reviewed_hash):
 require(len(raw)<=2*1024*1024 and SHA(raw)==reviewed_hash,'reviewed manifest hash mismatch/size')
 def unique(pairs):
  result={}
  for k,v in pairs:
   require(k not in result,'duplicate manifest key');result[k]=v
  return result
 m=json.loads(raw,object_pairs_hook=unique)
 require(set(m)=={'version','approved','identity','geometry','recovery_sha256','images','backup_receipts','migration','footer_review','parent_runtime_gates'},'manifest fields')
 require(m['version']==1 and m['approved'] is True,'unapproved manifest')
 require(m['geometry']==PARTS,'exact GPT geometry mismatch')
 require(m['identity']['serial']==SERIAL and m['identity']['gpt_sha256']==GPT,'device/GPT mismatch')
 require(re.fullmatch('[0-9a-f]{32}',m['identity'].get('emmc_cid','') or '') is not None,'unresolved eMMC CID')
 require(digest_ok(m['recovery_sha256']),'unreviewed dedicated rescue hash')
 require(m['parent_runtime_gates']==dict(recovery_authenticated=True,recovery_restore_tested=True,physical_reentry_tested=True,exclusive_writer=True),'runtime rescue gates absent')
 require(set(m['images'])=={'original_boot','original_system','candidate_boot','candidate_system','fresh_userdata','footer_magic'},'image allowlist')
 for name,image in m['images'].items():
  if image is None:continue
  require(set(image)=={'bytes','sha256','chunks'},'image fields')
  part='userdata' if name=='fresh_userdata' else 'boot' if name.endswith('boot') else 'system'
  size=4 if name=='footer_magic' else PARTS[part]['sectors']*512
  require(type(image['bytes']) is int and image['bytes']==size and digest_ok(image['sha256']),'image bytes/hash')
  require(len(image['chunks'])==(size+CHUNK-1)//CHUNK and all(digest_ok(x) for x in image['chunks']),'bounded chunk map')
 require(m['images']['original_boot'] is not None,'original boot required')
 require(m['images']['original_boot']['sha256']==ORIGINAL_BOOT,'original boot mismatch')
 require(m['images']['original_system'] is not None,'verified original SYSTEM required')
 for part in ('boot','system','recovery'):
  receipt=m['backup_receipts'].get(part,{})
  expected=ORIGINAL_RECOVERY if part=='recovery' else m['images']['original_'+part]['sha256']
  require(receipt.get('sha256')==expected and receipt.get('bytes')==PARTS[part]['sectors']*512 and receipt.get('source_read_twice') is True and receipt.get('durable_destination_reread') is True and receipt.get('parent_verified') is True,'missing durable backup receipt '+part)
 require(type(m['migration']) is bool and type(m['footer_review']) is bool,'review flags must be bool')
 if m['footer_review']:
  receipt=m['backup_receipts'].get('metadata',{})
  require(m['migration'] and receipt.get('bytes')==33554432 and digest_ok(receipt.get('sha256')) and receipt.get('source_read_twice') is True and receipt.get('parent_verified') is True,'reviewed original metadata receipt required')
 return ReviewedManifest(m)

class Geometry(ctypes.Structure):
 _fields_=[('start',ctypes.c_ulonglong),('sectors',ctypes.c_ulonglong),('partition',ctypes.c_uint),('major',ctypes.c_uint),('minor',ctypes.c_uint),('logical_sector',ctypes.c_uint)]
class NativeGate:
 def __init__(self,path):
  self.lib=ctypes.CDLL(str(path));self.lib.rescue_geometry.argtypes=[ctypes.c_uint,ctypes.POINTER(Geometry)]
  self.lib.rescue_frame.argtypes=[ctypes.c_uint,ctypes.c_ulonglong,ctypes.c_ulonglong,ctypes.c_ulonglong]+[ctypes.c_uint]*6
 def geometry(self,op,g):return bool(self.lib.rescue_geometry(op,ctypes.byref(Geometry(**g))))
 def frame(self,op,off,n,expected,uid,domain,migration,footer):
  return bool(self.lib.rescue_frame(op,off,n,expected,1,uid,int(domain=='u:r:shell:s0'),1,int(migration),int(footer)))

@dataclass(frozen=True)
class Peer:
 uid:int
 domain:str
 # Actual Linux adapter must obtain both from SO_PEERCRED/SO_PEERSEC; wire claims forbidden.

class Session:
 """One operation, one connection, no resume. Every terminal state rejects calls.
 A caller passes a PARSED and parent-hash-pinned manifest. No input paths from wire.
 backend methods: identity, geometry, alias_matches, unmounted, recovery_hash,
 read_at(part,off,count), write_at(part,off,bytes), flush, journal(event).
 A read/write/flush/journal exception after arming is uncertainty and freezes I/O.
 """
 def __init__(self,manifest,gate,backend,peer,*,execute=False):
  require(isinstance(manifest,ReviewedManifest),'manifest must be independently hash-validated')
  self.m=manifest;self.g=gate;self.b=backend;self.peer=peer
  self.state=State.PLAN;self.writes=0;self.offset=0;self.operation=None
  self.execute=execute;self.image=None
 def guard(self,part,op):
  require(self.peer.uid==2000 and self.peer.domain=='u:r:shell:s0','peer credentials')
  require(self.b.identity()==self.m['identity'],'physical device/CID/GPT identity')
  require(self.g.geometry(op,self.b.geometry(part)),'partition geometry')
  require(self.b.alias_matches(part),'alias and opened node st_rdev mismatch')
  require(self.b.unmounted(part),'partition mounted or has holders')
  require(self.b.recovery_hash()==self.m['recovery_sha256'],'dedicated recovery changed')
 def frozen(self):require(self.state not in (State.DONE,State.UNCERTAIN,State.FAILED),'terminal session; no retries')
 def uncertain(self):self.state=State.UNCERTAIN
 def hash_current(self,part,size):
  h=hashlib.sha256()
  for off in range(0,size,CHUNK):
   count=min(CHUNK,size-off);data=self.b.read_at(part,off,count)
   if len(data)!=count:raise TransportLost('short full readback')
   h.update(data)
  return h.hexdigest()
 def begin(self,operation,*,system_verified=False,data_verified=False):
  self.frozen();require(self.state==State.PLAN,'already started')
  require(operation in OPS,'unknown operation')
  op,part,key=OPS[operation];self.operation=operation
  if not self.execute:return {'mode':'PLAN_ONLY','operation':operation,'partition':part,'no_io':True}
  require(self.m.get('approved') is True,'unapproved')
  require(operation not in ('provision-data','invalidate-footer-magic') or self.m['migration'],'clean data migration not reviewed')
  require(operation!='invalidate-footer-magic' or self.m['footer_review'],'footer operation not reviewed')
  require(operation!='install-boot' or (system_verified and data_verified),'install BOOT last after SYSTEM and DATA full verification')
  self.image=self.m['images'][key];require(self.image is not None,'no reviewed image')
  try:
   self.guard(part,op)
   self.b.journal({'state':'ARMED','operation':operation,'expected':self.image['sha256']})
   self.state=State.ARMED
   if operation.startswith('restore-'):
    if self.hash_current(part,self.image['bytes'])==self.image['sha256']:
     self.b.journal({'state':'ALREADY_ORIGINAL','operation':operation});self.state=State.DONE;return 'already-original'
   if operation.startswith('install-'):
    require(self.hash_current(part,self.image['bytes'])==self.m['images']['original_'+part]['sha256'],'install requires exact original partition')
   if operation=='invalidate-footer-magic':
    require(self.b.read_at('metadata',0,4)==bytes.fromhex('c4b1b5d0'),'unexpected footer magic')
    self.metadata_before=self.hash_current('metadata',PARTS['metadata']['sectors']*512)
    require(self.metadata_before==self.m['backup_receipts'].get('metadata',{}).get('sha256'),'reviewed metadata snapshot mismatch')
   return 'armed'
  except Refused:self.state=State.FAILED;raise
  except Exception:self.uncertain();raise
 def feed(self,index,data):
  self.frozen();require(self.execute and self.state in (State.ARMED,State.WRITING),'not armed')
  op,part,_=OPS[self.operation]
  try:
   require(type(data) is bytes and index==self.offset//CHUNK,'frame sequence')
   n=min(CHUNK,self.image['bytes']-self.offset)
   require(n>0 and len(data)==n,'frame byte count')
   require(self.g.frame(op,self.offset,n,self.offset,self.peer.uid,self.peer.domain,self.m['migration'],self.m['footer_review']),'native fixed bounds gate')
   require(SHA(data)==self.image['chunks'][index],'frame digest mismatch before write')
   if op==6:require(data==bytes(4),'footer operation only invalidates four-byte magic')
   self.guard(part,op)
   self.b.journal({'state':'WRITE_INTENT','offset':self.offset,'bytes':n,'operation':self.operation})
   self.state=State.WRITING;self.writes+=1
   written=self.b.write_at(part,self.offset,data)
   if written!=n:raise TransportLost('short/ambiguous write; no retry')
   self.offset+=n
  except Refused:self.state=State.FAILED;raise
  except Exception:self.uncertain();raise
 def finish(self):
  self.frozen();require(self.state==State.WRITING,'not writing')
  op,part,_=OPS[self.operation]
  try:
   require(self.offset==self.image['bytes'],'incomplete transfer')
   self.b.flush(part);self.state=State.VERIFYING;self.guard(part,op)
   require(self.hash_current(part,self.image['bytes'])==self.image['sha256'],'full readback hash mismatch')
   if op==6:
    # Full metadata readback with ONLY original magic logically substituted must match baseline.
    h=hashlib.sha256();size=PARTS['metadata']['sectors']*512
    for off in range(0,size,CHUNK):
     data=self.b.read_at(part,off,min(CHUNK,size-off))
     require(len(data)==min(CHUNK,size-off),'short metadata readback')
     h.update(bytes.fromhex('c4b1b5d0')+data[4:] if off==0 else data)
    require(h.hexdigest()==self.metadata_before,'bytes outside footer magic changed')
   self.b.journal({'state':'FULL_READBACK_VERIFIED','operation':self.operation,'sha256':self.image['sha256']})
   self.state=State.DONE;return self.state.value
  except Refused:self.state=State.FAILED;raise
  except Exception:self.uncertain();raise
 def readback(self,part,sink):
  self.frozen();require(self.state==State.PLAN and part in READOPS,'readback scope/state')
  if not self.execute:return {'mode':'PLAN_ONLY','readback':part,'no_io':True}
  require(part not in ('userdata','metadata') or self.m['migration'],'data readback scope not reviewed')
  op=READOPS[part];size=PARTS[part]['sectors']*512;h=hashlib.sha256()
  try:
   self.guard(part,op);self.state=State.VERIFYING
   for off in range(0,size,CHUNK):
    data=self.b.read_at(part,off,min(CHUNK,size-off))
    if len(data)!=min(CHUNK,size-off):raise TransportLost('short readback')
    require(self.g.frame(op,off,len(data),off,self.peer.uid,self.peer.domain,self.m['migration'],self.m['footer_review']),'readback bounds')
    h.update(data);sink(off,data,SHA(data))
   self.b.journal({'state':'READBACK_STREAM_COMPLETE','partition':part,'bytes':size,'sha256':h.hexdigest(),'durable_destination_verified':False})
   self.state=State.DONE;return {'bytes':size,'sha256':h.hexdigest(),'durable_destination_verified':False}
  except Refused:self.state=State.FAILED;raise
  except Exception:self.uncertain();raise
 def lost(self):
  self.frozen();self.uncertain() # No further backend calls, including cleanup or inverse.

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True)
 ap.add_argument('--reviewed-sha256');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 require(not a.execute,'No Linux/ADB execution adapter is supplied; parent integration remains required')
 raw=a.manifest.read_bytes()
 if a.reviewed_sha256:parse_manifest(raw,a.reviewed_sha256)
 print(json.dumps({'mode':'PLAN_ONLY','manifest_sha256':SHA(raw),'device_contacted':False,'operations':OPS,'readback_partitions':list(READOPS),'runtime_adapter':'not implemented; not flash-ready'},indent=2))
if __name__=='__main__':main()
