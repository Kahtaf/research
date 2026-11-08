"""Exact compositional guards for r3; no permissive candidate re-binding."""
import gzip,hashlib,json,tarfile
from pathlib import Path

SENSOR_SUFFIX=b'\n$(call inherit-product, device/asus/p00a/sensors/sensors.mk)\n'
BOARD_SUFFIX=b'\ninclude device/asus/p00a/sensors/BoardConfig.mk\n'
PLATFORM={
 'platform_bpf':{'relative':'loader/bpfloader.rs','before':'1548dffa03b5091bbb9b7cfcce92495ee2167f417e90b431117cf31ea77b4bd2','after':'babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250','patch':'2ffaf6c9349c06394d8d5e2e4e2bd70104725a2665f644dc0f1ae4f07988d502'},
 'vold':{'relative':'model/PublicVolume.cpp','before':'0e17fccedefabb20e2d8650252af8c765af68378a1d853e0fbaa6a8bd1ea67fd','after':'c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9','patch':'98e923b851c0de58d4ca7787628f2fb4ea6471fd1cf2a36fe44c6482061168af'}}

def sensor_selection(plan, staged):
 from integrate import need,read,manifest,item,sha
 receipt=read(plan['sensor_receipt']);r2=read(plan['previous_staged_receipt'])
 origin=Path(plan['sensor_origin']);candidate=Path(plan['staging'])/'product-device'
 need(len(receipt['original_files'])==12,'Sensor selection must contain exactly 12 original sources')
 need(manifest(origin)==receipt['original_files'],'Sensor original source selection drift')
 expected=dict(receipt['original_files'])
 mk=(origin/'sensors.mk').read_bytes()
 for module in [b'android.hardware.sensors@1.0-service',b'android.hardware.sensors@1.0-impl']:
  need(mk.count(module)==1,'Sensor architecture selection ambiguous');mk=mk.replace(module,module+b':64')
 expected['sensors.mk']={'sha256':hashlib.sha256(mk).hexdigest()}
 need(expected==receipt['files']==manifest(candidate/'sensors'),'Exact sensor source/ARM64 package selection mismatch')
 lines=[l for l in (origin/'ueventd.fragment.rc').read_text().splitlines() if l and not l.startswith('#')]
 need(len(lines)==5,'Sensor ueventd count mismatch')
 suffixes={'device.mk':SENSOR_SUFFIX,'BoardConfig.mk':BOARD_SUFFIX,'rootdir/ueventd.rc':('\n'+'\n'.join(lines)+'\n').encode()}
 need(receipt['suffixes']=={p:s.decode() for p,s in suffixes.items()},'Sensor suffix selection changed')
 for rel,suffix in suffixes.items():
  base=Path(plan['previous_product_inputs'])/rel
  need(sha(base)==receipt['base_sha256'][rel]==r2['product_after'][rel]['sha256'],'r2 composition preimage mismatch '+rel)
  need((candidate/rel).read_bytes()==base.read_bytes()+suffix,'Exact r2 + sensor composition mismatch '+rel)
  need(sha(candidate/rel)==receipt['after_sha256'][rel]==staged['product_after'][rel]['sha256'],'Sensor composition postimage mismatch '+rel)
 for rel,expected_hash in expected.items():need(staged['product_after'].get('sensors/'+rel)==expected_hash,'Sensor staged manifest mismatch')
 return {'sensors/'+p for p in expected}

def source_composition(plan, source):
 from integrate import need,read
 old=read(plan['previous_source_receipt']);delta=read(plan['kernel_delta']);baseline=read(plan['snapshot'])['files']
 need(len(old['changes'])==268 and len(delta)==9,'Wrong source handoff sizes')
 expected={k:dict(v) for k,v in old['changes'].items()}
 for rel,change in delta.items():
  need(change['before']==old['changes'].get(rel,{}).get('after',baseline.get(rel)),'BMC r5-relative preimage mismatch '+rel)
  expected[rel]={'before':baseline.get(rel),'after':change['after']}
 need(len(expected)==276 and source['changes']==expected,'276-file kernel composition mismatch')
 return len(expected)

def platform_selection(plan, phase='before'):
 from integrate import need,read,item,safe,manifest
 records={}
 for name,pin in PLATFORM.items():
  receipt=read(plan[name+'_receipt']);expected={pin['relative']:{'before':pin['before'],'after':pin['after']}}
  need(receipt['files']==expected and receipt['patch_sha256']==pin['patch'],'Exact one-file '+name+' selection mismatch')
  staged=Path(plan[name+'_staged'])
  need(manifest(staged)=={pin['relative']:{'sha256':pin['after']}},name+' staged postimage mismatch')
  if name=='vold':
   data=(staged/pin['relative']).read_bytes()
   need(data.count(b'#include <algorithm>\n')==1 and hashlib.sha256(data.replace(b'#include <algorithm>\n',b'',1)).hexdigest()==pin['before'],'vold must be the sole algorithm include addition')
  need(item(safe(plan[name],pin['relative']))=={'sha256':pin[phase]},name+' active '+phase+'image mismatch')
  records[name]={'files':expected,'patch_sha256':pin['patch'],'receipt_sha256':__import__('integrate').sha(plan[name+'_receipt'])}
 return records

def platform_destinations(plan):
 from integrate import safe
 return [(safe(plan[n],p['relative']),n+'/'+p['relative']) for n,p in PLATFORM.items()]

def apply_platform(plan):
 from integrate import copy_exact,safe
 for name,pin in PLATFORM.items():copy_exact(safe(plan[name+'_staged'],pin['relative']),safe(plan[name],pin['relative']),{'sha256':pin['after']})

def verify_bundle(plan):
 from integrate import need,read
 manifest=read(plan['bpf_supplement_manifest']);count=0
 with tarfile.open(plan['bpf_supplement_archive'],'r:gz') as tar:
  # The qualified archive has one named top-level directory. Never extract ELFs.
  all_members=tar.getmembers()
  need(len({m.name for m in all_members})==len(all_members),'Duplicate supplement archive member')
  need(all(not m.issym() and not m.islnk() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in all_members),'Unsafe supplement member')
  members={m.name:m for m in all_members}
  matched=set()
  for rel,entry in manifest['files'].items():
   matches=[m for name,m in members.items() if name==rel or name.endswith('/'+rel)]
   need(len(matches)==1 and matches[0].isfile(),'Ambiguous/missing qualified supplement entry '+rel)
   matched.add(matches[0].name)
   h=hashlib.sha256();size=0
   with tar.extractfile(matches[0]) as f:
    for block in iter(lambda:f.read(1048576),b''):h.update(block);size+=len(block)
   need(h.hexdigest()==entry['sha256'] and size==entry['bytes'],'Qualified supplement changed '+rel);count+=1
  extras={m.name for m in all_members if m.isfile()}-matched
  need(len(extras)==1,'Unexpected supplement files')
  extra=next(iter(extras))
  with tar.extractfile(members[extra]) as f: need(json.load(f)==manifest,'Supplement internal manifest mismatch')
  if 'bpf_qualified_selection' in plan:
   rel=manifest['authoritative_selection']
   match=next(m for n,m in members.items() if n.endswith('/'+rel))
   with tar.extractfile(match) as f:need(json.load(f)==read(plan['bpf_qualified_selection']),'Supplement selection mismatch')
 need(count==201,'Qualified supplement is incomplete')
 return count

def complete_kernel(plan):
 from integrate import need,sha
 expected=json.loads(gzip.decompress(Path(plan['complete_kernel_manifest']).read_bytes()))
 root=Path(plan['compiled_fixture']);actual=set()
 for p in root.rglob('*'):
  if p.is_file() and not p.is_symlink():
   rel=str(p.relative_to(root));actual.add(rel);need(expected.get(rel)==sha(p),'Complete compiled source mismatch '+rel)
 need(actual==set(expected),'Compiled source file set mismatch')
 return len(actual)
