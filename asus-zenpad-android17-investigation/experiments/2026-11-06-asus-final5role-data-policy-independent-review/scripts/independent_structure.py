"""Independent encoded-policy projection and xperm oracle.
Prefix decoder adapted from prior public review, not the corrected auditor.
No policy writes: only JSON evidence. Pinned version-30 layout only.
"""
from pathlib import Path
import json,struct,hashlib,time
R=Path(__file__).resolve().parents[1]
def decode(path):
 b=path.read_bytes(); started=time.monotonic()
 class Reader:
  def __init__(self,pos=0):self.pos=pos
  def take(self,n):
   assert 0<=n<=len(b)-self.pos
   out=b[self.pos:self.pos+n];self.pos+=n;return out
  def nums(self,n=1,fmt='I'):return struct.unpack('<'+fmt*n,self.take(struct.calcsize('<'+fmt*n)))
  def u(self):return self.nums()[0]
  def text(self,n):return self.take(n).decode('ascii')
  def bitmap(self):
   mapsize,highbit,count=self.nums(3);assert mapsize==64 and count<=1000 and highbit%64==0
   assert (highbit==0)==(count==0);bits=set();last=-64
   for _ in range(count):
    start=self.u();value=self.nums(fmt='Q')[0];assert value and start%64==0 and last<start<highbit
    last=start;bits.update(start+i for i in range(64) if value&(1<<i))
   if count:assert highbit==last+64
   return bits
  def level(self):self.u();self.bitmap()
  def range(self):
   count=self.u();assert count in (1,2);self.nums(count);self.bitmap()
   if count==2:self.bitmap()
  def constraints(self,count):
   for _ in range(count):
    _,nexpr=self.nums(2)
    for _ in range(nexpr):
     expr,_,_=self.nums(3)
     if expr==5:self.bitmap();self.bitmap();self.bitmap();self.u()
 r=Reader();assert r.u()==0xf97cff8c and r.text(r.u())=='SE Linux'
 version,config,symnum,oconnum=r.nums(4);assert version==30 and symnum==8
 caps=r.bitmap();permissive=r.bitmap();tables=[{} for _ in range(8)];prim=[]
 def perms(count):
  out={}
  for _ in range(count):n,value=r.nums(2);out[r.text(n)]=value
  return out
 for table in range(8):
  nprim,nel=r.nums(2);prim.append(nprim);assert nel<10000
  for _ in range(nel):
   if table==0:
    n,value,_,count=r.nums(4);name=r.text(n);datum=dict(value=value,permissions=perms(count))
   elif table==1:
    n,cn,value,_,count,ncons=r.nums(6);name=r.text(n);common=r.text(cn);permissions=perms(count)
    if common:permissions.update(tables[0][common]['permissions'])
    r.constraints(ncons);r.constraints(r.u());r.nums(4);datum=dict(value=value,permissions=permissions)
   elif table==2:
    n,value,bounds=r.nums(3);name=r.text(n);r.bitmap();r.bitmap();datum=dict(value=value,bounds=bounds)
   elif table==3:
    n,value,properties,bounds=r.nums(4);name=r.text(n);datum=dict(value=value,properties=properties,bounds=bounds)
   elif table==4:
    n,value,bounds=r.nums(3);name=r.text(n);r.bitmap();r.range();r.level();datum=dict(value=value,bounds=bounds)
   elif table==5:value,state,n=r.nums(3);name=r.text(n);datum=dict(value=value,state=state)
   elif table==6:n,alias=r.nums(2);name=r.text(n);r.level();datum=dict(alias=alias)
   else:n,value,alias=r.nums(3);name=r.text(n);datum=dict(value=value,alias=alias)
   tables[table][name]=datum
 av_start=r.pos;count=r.u();assert count<100000;rules=[]
 for _ in range(count):
  start=r.pos;source,target,cls,specified=r.nums(4,'H');rule=dict(source=source,target=target,cls=cls,specified=specified)
  if specified&0x700:
   kind,driver=r.nums(2,'B');values=r.nums(8)
   rule.update(kind=kind,driver=driver,functions=[j for j in range(256) if values[j//32]&(1<<(j%32))])
  else:rule['data']=r.u()
  rule.update(start=start,end=r.pos);rules.append(rule)
 av_end=r.pos;assert r.u()==0
 end=len(b);attrs=[]
 for _ in range(prim[3]):
  assert time.monotonic()-started<15;candidates=[]
  for count in range((prim[3]+63)//64+1):
   start=end-12*(count+1)
   if start<av_end:continue
   if struct.unpack_from('<I',b,start)[0]!=64 or struct.unpack_from('<I',b,start+8)[0]!=count:continue
   try:
    rr=Reader(start);bits=rr.bitmap()
    if rr.pos==end and all(i<prim[3] for i in bits):candidates.append((start,bits))
   except AssertionError:pass
  assert len(candidates)==1,(end,len(candidates));end,bits=candidates[0];attrs.append(bits)
 attrs.reverse()
 return dict(b=b,tables=tables,attrs=attrs,rules=rules,av_start=av_start,av_end=av_end,permissive=permissive,version=version)
def main():
 f=decode(R/'inputs/restore-sepolicy');p=decode(R/'inputs/reviewed-policy');types=p['tables'][3];bc=p['tables'][1]['blk_file'];s=types['os_rescue']['value'];t=types['rescue_userdata_device']['value']
 added=[r for r in p['rules'] if (r['source'],r['target'],r['cls'])==(s,t,bc['value'])]
 assert len(added)==2
 av,xp=sorted(added,key=lambda r:r['specified'])
 mask=sum(1<<(bc['permissions'][n]-1) for n in ['open','read','write','getattr','ioctl'])
 assert av['specified']==1 and av['data']==mask
 assert xp['specified']==0x100 and xp['kind']==1 and xp['driver']==0x12 and xp['functions']==[0x72]
 projected=p['b'][:p['av_start']]+struct.pack('<I',len(p['rules'])-2)+b''.join(p['b'][r['start']:r['end']] for r in p['rules'] if r not in added)+p['b'][p['av_end']:]
 assert projected==f['b'],'raw byte projection differs'
 actors=['os_rescue','p10_restore'];nodes=['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device','rescue_userdata_device']
 details={}
 for name in actors+nodes:
  d=types[name];i=d['value'];assert not d['bounds'] and i not in p['permissive'] and p['attrs'][i-1]=={i-1}
  details[name]=dict(type=i,bounds=0,permissive=False,attributes=[name])
 rows=[]
 for actor in actors:
  for node in nodes:
   sid=types[actor]['value'];tid=types[node]['value']
   matches=[r for r in p['rules'] if r['specified']==0x100 and r['source']-1 in p['attrs'][sid-1] and r['target']-1 in p['attrs'][tid-1] and r['cls']==bc['value']]
   allowed=set()
   for r in matches:
    assert r['kind'] in (1,2)
    if r['kind']==1:allowed.update((r['driver']<<8)|v for v in r['functions'])
    else:allowed.update((v<<8)|j for v in r['functions'] for j in range(256))
   assert allowed==({0x1272} if actor!='p10_restore' or node!='rescue_userdata_device' else set())
   rows.append(dict(source=actor,target=node,matching_xperm_rules=len(matches),allowed_keys=sorted(allowed)))
 result=dict(passed=True,method='Independent encoded byte projection, no libsepol reserialization',candidate_bytes=len(p['b']),candidate_sha256=hashlib.sha256(p['b']).hexdigest(),projected_bytes=len(projected),projected_sha256=hashlib.sha256(projected).hexdigest(),av_delta_mask=mask,removed_entries=added,all_remaining_encoded_bytes_identical=True,conditionals=0,details=details,ioctl_rows=rows,scope='Actual pinned policy30; native AV decisions separately checked; ioctl values are low16 SELinux keys, not full command encodings or runtime acceptance')
 (R/'evidence/independent-structure.json').write_text(json.dumps(result,indent=2)+'\n');print('RAW_PROJECTION_PASS',len(projected),result['projected_sha256'])
if __name__=='__main__':main()
