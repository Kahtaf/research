"""Exact-input policy30 binary inspection; no policy output or compilation.

The prefix layout follows vendored libsepol policydb.c/avtab.c/ebitmap.c.
Effective AVs come separately from the existing native libsepol query.
This checks xperm tables, zero conditionals, bounds, permissive bits and the
unique trailing type-attribute map, including inherited xperm matches.
It is deliberately not a general SELinux policy evaluator.
"""
from pathlib import Path
import hashlib
import json
import struct
import time

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parents[1]
P = ROOT/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/restore-sepolicy'
b = P.read_bytes()
assert len(b) < 8*1024**2
assert hashlib.sha256(b).hexdigest() == '16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2'
started = time.monotonic()

class Reader:
    def __init__(self, pos=0): self.pos = pos
    def take(self, n):
        assert 0 <= n <= len(b)-self.pos
        out=b[self.pos:self.pos+n]; self.pos+=n; return out
    def nums(self, n=1, fmt='I'): return struct.unpack('<'+fmt*n, self.take(struct.calcsize('<'+fmt*n)))
    def u(self): return self.nums()[0]
    def text(self,n): return self.take(n).decode('ascii')
    def bitmap(self):
        mapsize, highbit, count = self.nums(3)
        assert mapsize==64 and count <= 1000 and highbit%64==0
        assert (highbit==0)==(count==0)
        bits=set(); last=-64
        for _ in range(count):
            start=self.u(); value=self.nums(fmt='Q')[0]
            assert value and start%64==0 and last<start<highbit
            last=start
            bits.update(start+i for i in range(64) if value & (1<<i))
        if count: assert highbit==last+64
        return bits
    def level(self): self.u(); self.bitmap()
    def range(self):
        count=self.u(); assert count in (1,2)
        self.nums(count); self.bitmap()
        if count==2: self.bitmap()
    def constraints(self,count):
        for _ in range(count):
            _, nexpr=self.nums(2)
            for _ in range(nexpr):
                expr,_,_=self.nums(3)
                if expr==5:
                    self.bitmap(); self.bitmap(); self.bitmap(); self.u()

r=Reader()
assert r.u()==0xf97cff8c
assert r.text(r.u())=='SE Linux'
version,config,symnum,oconnum=r.nums(4)
assert version==30 and symnum==8
caps=r.bitmap(); permissive=r.bitmap()
tables=[{} for _ in range(8)]; prim=[]

def perms(count):
    out={}
    for _ in range(count):
        n,value=r.nums(2);out[r.text(n)]=value
    return out

for table in range(8):
    nprim, nel=r.nums(2); prim.append(nprim)
    assert nel < 10000
    for _ in range(nel):
        if table==0:
            n,value,_,count=r.nums(4);name=r.text(n)
            datum=dict(value=value,permissions=perms(count))
        elif table==1:
            n,cn,value,_,count,ncons=r.nums(6)
            name=r.text(n);common=r.text(cn)
            permissions=perms(count)
            if common: permissions.update(tables[0][common]['permissions'])
            r.constraints(ncons);r.constraints(r.u());r.nums(4)
            datum=dict(value=value,permissions=permissions)
        elif table==2:
            n,value,bounds=r.nums(3);name=r.text(n);r.bitmap();r.bitmap()
            datum=dict(value=value,bounds=bounds)
        elif table==3:
            n,value,properties,bounds=r.nums(4);name=r.text(n)
            datum=dict(value=value,properties=properties,bounds=bounds)
        elif table==4:
            n,value,bounds=r.nums(3);name=r.text(n);r.bitmap();r.range();r.level()
            datum=dict(value=value,bounds=bounds)
        elif table==5:
            value,state,n=r.nums(3);name=r.text(n);datum=dict(value=value,state=state)
        elif table==6:
            n,alias=r.nums(2);name=r.text(n);r.level();datum=dict(alias=alias)
        else:
            n,value,alias=r.nums(3);name=r.text(n);datum=dict(value=value,alias=alias)
        tables[table][name]=datum

av_start=r.pos
count=r.u();assert count<100000
rules=[]
for _ in range(count):
    source,target,cls,specified=r.nums(4,'H')
    if specified&0x700:
        kind,driver=r.nums(2,'B');values=r.nums(8)
        rules.append(dict(source=source,target=target,cls=cls,specified=specified,
                          kind=kind,driver=driver,functions=[j for j in range(256) if values[j//32]&(1<<(j%32))]))
    else:
        rules.append(dict(source=source,target=target,cls=cls,specified=specified,data=r.u()))
av_end=r.pos
assert r.u()==0, 'Nonempty conditional table unsupported; refuse inference'

# Read the final nprim type-attribute maps backwards, requiring a unique valid
# preceding bitmap at every step. There are no bytes after this table in the
# exact policydb_read layout. The native query independently loads the whole file.
end=len(b);attrs=[]
for _ in range(prim[3]):
    assert time.monotonic()-started<10
    candidates=[]
    for count in range((prim[3]+63)//64+1):
        start=end-12*(count+1)
        if start < av_end: continue
        if struct.unpack_from('<I',b,start)[0]!=64: continue
        if struct.unpack_from('<I',b,start+8)[0]!=count: continue
        try:
            rr=Reader(start);bits=rr.bitmap()
            if rr.pos==end and all(i<prim[3] for i in bits): candidates.append((start,bits))
        except AssertionError: pass
    assert len(candidates)==1, (end,len(candidates))
    end,bits=candidates[0];attrs.append(bits)
attrs.reverse()
types=tables[3];type_names={v['value']:k for k,v in types.items() if v['properties']&1}
actors=['init','ueventd','adbd','shell','os_rescue','p10_restore']
nodes=['rescue_recovery_device','rescue_disk_device','block_device','rescue_boot_device','rescue_system_device','rescue_userdata_device']
av=json.loads((OWN/'evidence/effective-policy.json').read_text())['rows']
rows=[]
for actor in actors:
    s=types[actor]['value'];sa=attrs[s-1]|{s-1}
    for node in nodes:
        t=types[node]['value'];ta=attrs[t-1]|{t-1}
        matches=[rule for rule in rules if rule['source']-1 in sa and rule['target']-1 in ta and rule['cls']==tables[1]['blk_file']['value'] and rule['specified']==0x100]
        ioctls=set()
        for rule in matches:
            if rule['kind']==1: ioctls.update((rule['driver']<<8)|j for j in rule['functions'])
            elif rule['kind']==2: ioctls.update((driver<<8)|j for driver in rule['functions'] for j in range(256))
            else: raise AssertionError('unknown xperm kind')
        decision=next(row for row in av if row['source']==f'u:r:{actor}:s0' and row['target']==f'u:object_r:{node}:s0' and row['cls']=='blk_file')
        allowed='ioctl' in decision['allowed']
        # No extended-permission match with coarse ioctl allowed means no xperm
        # whitelist applies; it does NOT mean deny-all (e.g. stock init/generic).
        effective='DENIED_BASE_AV' if not allowed else sorted(hex(i) for i in ioctls) if matches else 'NO_XPERM_WHITELIST'
        rows.append(dict(source=actor,target=node,base_ioctl=allowed,effective_ioctl=effective,
                         matched_xperm_rules=matches))

details={name:dict(type=types[name],attributes=[type_names.get(i+1,str(i+1)) for i in sorted(attrs[types[name]['value']-1]|{types[name]['value']-1})],
                   permissive=types[name]['value'] in permissive)
         for name in actors+nodes}
for name in ['os_rescue','p10_restore']+nodes[:2]+nodes[3:]:
    assert details[name]['attributes']==[name] and not details[name]['permissive'] and not details[name]['type']['bounds']
result=dict(policy_sha256=hashlib.sha256(b).hexdigest(),policy_bytes=len(b),version=version,
            config=config,type_count=prim[3],avtab_rules=len(rules),avtab_offsets=[av_start,av_end],
            conditionals=0,type_attribute_tail_offset=end,details=details,rows=rows,
            parser_scope='Exact-policy structural supplement to native effective AV query; not a general policy evaluator')
(OWN/'evidence/policy-xperms.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('details','rows')}))
for row in rows:
    if row['source'] in ('os_rescue','p10_restore') or row['target']=='rescue_userdata_device':
        print(row['source'],row['target'],row['effective_ioctl'])
