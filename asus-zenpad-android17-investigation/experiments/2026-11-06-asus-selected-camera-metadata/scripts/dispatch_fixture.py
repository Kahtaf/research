"""Run pinned ARM32 dispatch instructions in Unicorn, never native vendor code.
Only whitelisted instruction ranges run. All imports and constructor calls are
Python stubs. No emulator syscall hook, host dlopen, sensor or property access.
"""
from analyze import Binary,ROOT
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
import json,hashlib,importlib.metadata
REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]
class Fixture:
 def __init__(self,library='lib_libcam.metadataprovider.so',symbols=None,dlopen_ok=True):
  self.b=Binary(ROOT/'inputs'/library);self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM);self.u.mem_map(0,0x600000)
  for s in self.b.e.iter_segments():
   if s['p_type']=='PT_LOAD':self.u.mem_write(s['p_vaddr'],s.data())
  self.heap=0x100000;self.next_stub=0x500000;self.stubs={};self.allowed=[];self.events=[];self.symbols=symbols or {};self.dlopen_ok=dlopen_ok;self.metadata={};self.entries={};self.vectors={};self.sensor_name='';self.sensor_type=0;self.sensor_dev=1;self.sensor_index=0;self.constructor_writes=[];self.converter_error=0;self.converter_null=False;self.dynamic={};self.dng={}
  for sec in self.b.e.iter_sections():
   if sec['sh_type']=='SHT_REL':
    for rel in sec.iter_relocations():
     if rel['r_info_sym']:
      sym=self.b.syms[rel['r_info_sym']]
      if sym['st_value']:self.put(rel['r_offset'],sym['st_value'])
      elif sym.name=='__stack_chk_guard':self.put(rel['r_offset'],self.alloc(b'\x7a\x71\x81\x91'))
  plt=self.b.e.get_section_by_name('.plt')['sh_addr']+20
  for i,r in enumerate(self.b.e.get_section_by_name('.rel.plt').iter_relocations()):self.stubs[plt+i*12]=self.b.syms[r['r_info_sym']].name
  self.stop=0x5ff000;self.u.hook_add(UC_HOOK_CODE,self.hook)
  self.meta_vtable=self.alloc(bytes(128));self.entry_vtable=self.alloc(bytes(128))
  for off,name in [(0xc,'meta_count'),(0x18,'meta_sort'),(0x1c,'meta_update')]:self.put(self.meta_vtable+off,self.stub(name))
  for off,name in [(8,'entry_tag'),(0xc,'entry_empty'),(0x2c,'entry_value'),(0x38,'entry_value')]:self.put(self.entry_vtable+off,self.stub(name))
  self.sensor=self.alloc(bytes(8));sv=self.alloc(bytes(128));self.put(self.sensor,sv)
  for off,name in [(0xc,'sensor_static'),(0x10,'sensor_name'),(0x14,'sensor_type'),(0x1c,'sensor_dev')]:self.put(sv+off,self.stub(name))
 def get(self,a):return int.from_bytes(self.u.mem_read(a,4),'little')
 def put(self,a,v):self.u.mem_write(a,int(v&0xffffffff).to_bytes(4,'little'))
 def alloc(self,data):
  a=self.heap;self.heap+=(len(data)+15)&~15;self.u.mem_write(a,data);return a
 def string(self,a):return bytes(self.u.mem_read(a,512)).split(b'\0')[0].decode()
 def stub(self,name):
  a=self.next_stub;self.next_stub+=4;self.stubs[a]=name;return a|1
 def find(self,part):
  ss=[s for s in self.b.syms if part in s.name and s['st_size']];assert len(ss)==1,(part,len(ss));return ss[0]
 def allow(self,part):
  s=self.find(part);self.allowed.append((s['st_value']&~1,(s['st_value']&~1)+s['st_size']));return s['st_value']
 def obj(self,kind):
  a=self.alloc(bytes(128));v=self.alloc(bytes(128));self.put(a,v)
  if kind=='static':methods={0x38:'26impConstructStaticMetadataE',0x3c:'40impConstructStaticMetadata_by_SymbolNameE'}
  elif kind=='request':methods={0x20:'24constructRequestMetadataE',0x24:'27impConstructRequestMetadataE',0x28:'41impConstructRequestMetadata_by_SymbolNameE',0x2c:'15TemplateRequest10updateDataE'}
  for off,part in methods.items():
   if off==0x2c and kind=='request':self.put(v+off,self.stub('request_update'))
   else:self.put(v+off,self.allow(part))
  return a
 def newmeta(self,a=None,values=None):
  if a is None:a=self.alloc(bytes(8))
  self.put(a,self.meta_vtable);self.metadata[a]=dict(values or {});return a
 def entry(self,tag,values):
  a=self.alloc(bytes(8));self.put(a,self.entry_vtable);self.entries[a]=(tag,list(values));return a
 def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v&0xffffffff);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
 def hook(self,u,a,size,_):
  if a==self.stop:u.emu_stop();return
  if a in self.stubs:
   n=self.stubs[a];r=[u.reg_read(x) for x in REGS];sp=u.reg_read(UC_ARM_REG_SP)
   if n=='_ZN7android7String86formatEPKcz':
    fmt=self.string(r[1]);args=[r[2],r[3]]+[self.get(sp+4*i) for i in range(6)];s=fmt%tuple(self.string(x) for x in args[:fmt.count('%s')]);self.put(r[0],self.alloc(s.encode()+b'\0'));self.ret(r[0]);return
   if n=='dlsym':
    name=self.string(r[1]);self.events.append({'event':'dlsym','handle':hex(r[0]),'symbol':name});self.ret(self.stub('constructor:'+name) if name in self.symbols else 0);return
   if n.startswith('constructor:'):
    name=n.split(':',1)[1];spec=self.symbols[name];status=spec.get('status',0);self.metadata.setdefault(r[0],{}).update(spec.get('writes',{}));self.events.append({'event':'constructor_stub','symbol':name,'second_arg':r[1],'status':status});self.ret(status);return
   if n=='dlopen':self.events.append({'event':'dlopen_stub','library':self.string(r[0]),'flags':r[1]});self.ret(0x123456 if self.dlopen_ok else 0);return
   if n in ['dlclose','dlerror','__android_log_print','_ZN7android7String8D1Ev','_ZN7android7RefBaseC2Ev','_ZN7android18NSMetadataProvider12showCustInfoEv','_ZN5NSCam9IMetadataD1Ev','_ZNK7android7RefBase9incStrongEPKv','_ZNK7android7RefBase9decStrongEPKv','_ZN5NSCam15IMetadataTagSetC1Ev','_ZN5NSCam15IMetadataTagSetD1Ev','request_update']:self.ret();return
   if n=='_Znwj':self.events.append({'event':'allocator_stub','bytes':r[0]});self.ret(self.alloc(bytes(r[0])));return
   if n=='_ZN7android16SortedVectorImplC2Ejj':self.vectors[r[0]]=[];self.ret(r[0]);return
   if n.startswith('tagset_'):
    self.events.append({'event':n,'tag':hex(r[1]),'arg2':self.string(r[2]) if n=='tagset_0x10' else hex(r[2]),'arg3':hex(r[3])});self.ret();return
   if n=='fopen':self.events.append({'event':'fopen_stub_denied','path':self.string(r[0])});self.ret(0);return
   if n=='meta_sort':self.events.append({'event':'metadata_sort_stub'});self.ret();return
   if n=='_ZN5NSCam9IMetadata6IEntryC1Ej':self.put(r[0],self.entry_vtable);self.entries[r[0]]=(r[1],[]);self.ret(r[0]);return
   if n=='_ZNK5NSCam9IMetadata6IEntry3tagEv':self.ret(self.entries[r[0]][0]);return
   if n=='_ZN5NSCam9IMetadata6IEntryD1Ev':self.ret();return
   if n.startswith('_ZN5NSCam9IMetadata6IEntry9push_back'):
    size=1 if 'ERKh' in n else 4
    self.entries[r[0]][1].append(int.from_bytes(self.u.mem_read(r[1],size),'little'));self.ret();return
   if n=='strerror':self.ret(self.alloc(b'stub_error\0'));return
   if n=='_ZN5NSCam14IHalSensorList3getEv':self.events.append({'event':'IHalSensorList_stub'});self.ret(self.sensor);return
   if n.startswith('sensor_'):
    self.events.append({'event':n,'index':r[1]})
    if n=='sensor_name':v=self.alloc(self.sensor_name.encode()+b'\0')
    elif n=='sensor_static':v=self.newmeta(values=self.dynamic)
    else:v=getattr(self,n)
    self.ret(v);return
   if n=='_ZN5NSCam9IMetadataC1Ev':self.newmeta(r[0]);self.ret(r[0]);return
   if n=='_ZN5NSCam9IMetadataC1ERKS0_':self.newmeta(r[0],self.metadata[r[1]]);self.ret(r[0]);return
   if n in ['_ZNK5NSCam9IMetadata5countEv','meta_count']:self.ret(len(self.metadata[r[0]]));return
   if n=='_ZNK5NSCam9IMetadata7isEmptyEv':self.ret(int(not self.metadata[r[0]]));return
   if n=='_ZNK5NSCam9IMetadata8entryForEj':self.ret(self.entry(r[1],self.metadata[r[0]].get(r[1],[])));return
   if n=='_ZNK5NSCam9IMetadata7entryAtEj':tag=list(self.metadata[r[0]])[r[1]];self.ret(self.entry(tag,self.metadata[r[0]][tag]));return
   if n=='meta_update':self.metadata[r[0]][r[1]]=self.entries[r[2]][1];self.ret();return
   if n=='entry_tag':self.ret(self.entries[r[0]][0]);return
   if n=='entry_empty':self.ret(int(not self.entries[r[0]][1]));return
   if n=='entry_value':
    vals=self.entries[r[0]][1];assert r[1]<len(vals),'missing entry access';self.ret(self.alloc(int(vals[r[1]]).to_bytes(4,'little')));return
   if n=='_ZN5NSCam9IMetadatapLERKS0_':self.metadata[r[0]].update(self.metadata[r[1]]);self.ret(r[0]);return
   if n=='_ZN6NS3Av37DngInfo11getInstanceEj':
    o=self.alloc(bytes(8));v=self.alloc(bytes(8));self.put(o,v);self.put(v,self.stub('dng_static'));self.events.append({'event':'DngInfo_stub','sensor_dev':r[0]});self.ret(o);return
   if n=='dng_static':self.newmeta(r[0],self.dng);self.ret(r[0]);return
   if n=='_ZN7android18NSMetadataProvider16MetadataProvider10updateDataERN5NSCam9IMetadataE':self.events.append({'event':'updateData_stub'});self.ret();return
   if n=='_ZN5NSCam18IMetadataConverter14createInstanceERKNS_15IMetadataTagSetE':
    c=self.converter();self.put(r[0],c);self.ret(r[0]);return
   if n=='converter_count':self.put(r[2],len(self.metadata[r[1]]));self.put(r[3],16);self.ret(self.converter_error);return
   if n=='converter_convert':
    self.events.append({'event':'allocator_converter_stub','metadata':self.metadata[r[1]],'null':self.converter_null});self.put(r[2],0 if self.converter_null else self.alloc(bytes(32)));self.ret(0 if self.converter_null else 1);return
   if n=='sort_camera_metadata':self.events.append({'event':'sort_stub','pointer_null':r[0]==0});self.ret();return
   if n=='_ZN7android16SortedVectorImpl3addEPKv':
    self.vectors.setdefault(r[0],[]).append((self.get(r[1]),self.get(r[1]+4)));self.ret(len(self.vectors[r[0]])-1);return
   if n=='_ZNK7android16SortedVectorImpl7indexOfEPKv':
    keys=[x[0] for x in self.vectors.get(r[0],[])];key=self.get(r[1]);self.ret(keys.index(key) if key in keys else -1);return
   raise AssertionError(('unstubbed import',n,hex(a),r))
  assert any(lo<=a<hi for lo,hi in self.allowed),('outside whitelist',hex(a))
 def converter(self):
  c=self.alloc(bytes(8));v=self.alloc(bytes(32));self.put(c,v);self.put(v+4,self.stub('converter_convert'));self.put(v+0xc,self.stub('converter_count'));return c
 def run(self,pc,*args):
  for i,v in enumerate(args):self.u.reg_write(REGS[i],v)
  self.u.reg_write(UC_ARM_REG_SP,0x3ff000);self.u.reg_write(UC_ARM_REG_LR,self.stop|1)
  self.u.emu_start(pc,self.stop,count=50000);assert self.u.reg_read(UC_ARM_REG_PC)==self.stop,('instruction bound',hex(self.u.reg_read(UC_ARM_REG_PC)))
  v=self.u.reg_read(UC_ARM_REG_R0);return v if v<0x80000000 else v-0x100000000
 def configured(self,sensor,kind):
  self.sensor_name=sensor;o=self.obj(kind)
  if kind=='static':
   self.run(self.allow('16MetadataProviderC1E'),o,0)
   # Constructor installs real vtable, whose imported/defined symbols were relocated.
  else:
   self.put(o+8,0);self.put(o+0xc,self.sensor_type);self.put(o+0x10,self.alloc(sensor.encode()+b'\0'))
  return o

def main():
 results=[]
 cats=['LENS','SENSOR','TUNING_3A','FLASHLIGHT','SCALER','FEATURE','CAMERA','REQUEST']
 for sensor in ['SENSOR_DRVNAME_OV5670_MIPI_RAW','SENSOR_DRVNAME_OV2680_MIPI_RAW']:
  for scenario,defs in [('all_missing',{}),('common_only',{'constructCustStaticMetadata_DEVICE_CAMERA_COMMON':{'writes':{0x1a0000:[0x100]}}}),('sensor_present',{'constructCustStaticMetadata_DEVICE_LENS_'+sensor:{'writes':{9:[1]}}}),('sensor_errors',{'constructCustStaticMetadata_DEVICE_LENS_'+sensor:{'status':-22,'writes':{9:[1]}},'constructCustStaticMetadata_DEVICE_LENS_COMMON':{'status':-5,'writes':{10:[2]}}})]:
   f=Fixture(symbols=defs);o=f.configured(sensor,'static');m=f.newmeta();rc=f.run(f.allow('26impConstructStaticMetadataE'),o,m)
   look=[e['symbol'] for e in f.events if e['event']=='dlsym'];expected=[]
   for family in ['DEVICE','PROJECT']:
    for cat in cats:
     n=f'constructCustStaticMetadata_{family}_{cat}_{sensor}';expected.append(n)
     if n not in defs or defs[n].get('status',0):expected.append(f'constructCustStaticMetadata_{family}_{cat}_COMMON')
   assert rc==0 and look==expected
   results.append({'sensor':sensor,'path':'static_dispatch','scenario':scenario,'return':rc,'metadata_stub':f.metadata[m],'events':f.events})
  for scenario,defs,expected in [('missing',{},-2),('sensor_present',{'constructCustRequestMetadata_'+sensor:{'writes':{1:[1]}}},0),('common_present',{'constructCustRequestMetadata_COMMON':{'writes':{1:[1]}}},0),('sensor_error_common_missing',{'constructCustRequestMetadata_'+sensor:{'status':-22}},-2),('sensor_error_common_error',{'constructCustRequestMetadata_'+sensor:{'status':-22},'constructCustRequestMetadata_COMMON':{'status':-5}},-5)]:
   for template in range(1,7):
    f=Fixture(symbols=defs);o=f.configured(sensor,'request');m=f.newmeta();rc=f.run(f.allow('27impConstructRequestMetadataE'),o,m,template);assert rc==expected
    results.append({'sensor':sensor,'path':'request_dispatch','scenario':scenario,'template':template,'return':rc,'events':f.events})
  for scenario,defs,expected in [('missing',{},-2),('common_present',{'constructCustRequestMetadata_COMMON':{'writes':{1:[1]}}},0),('converter_error',{'constructCustRequestMetadata_COMMON':{'writes':{1:[1]}}},-2147483648),('allocator_null',{'constructCustRequestMetadata_COMMON':{'writes':{1:[1]}}},0)]:
   f=Fixture(symbols=defs);o=f.configured(sensor,'request');m=f.newmeta();out=f.alloc(bytes(4));f.converter_error=int(scenario=='converter_error');f.converter_null=scenario=='allocator_null'
   # Tag-set population is an explicit schema stub, not metadata construction.
   f.stubs[0x246ec]='_ZN5NSCam15IMetadataTagSetC1Ev'
   rc=f.run(f.allow('24constructRequestMetadataE'),o,1,out,m);assert rc==expected
   results.append({'sensor':sensor,'path':'construct_request','scenario':scenario,'return':rc,'output_null':f.get(out)==0,'events':f.events})
 # Real COMMON body, with metadata containers and its fopen explicitly stubbed.
 for index in [0,1,2]:
  f=Fixture();m=f.newmeta();info=f.alloc(bytes(16));f.put(info,index);f.allowed.append((0x9970,0x99c4))
  rc=f.run(f.allow('constructCustStaticMetadata_DEVICE_CAMERA_COMMON'),m,info)
  assert rc==0 and f.metadata[m][0x1a0000]==[0x100]
  results.append({'path':'actual_common_body','synthetic_open_index':index,'return':rc,'metadata':{hex(k):v for k,v in f.metadata[m].items()},'events':f.events})
 for sensor in ['SENSOR_DRVNAME_OV5670_MIPI_RAW','SENSOR_DRVNAME_OV2680_MIPI_RAW']:
  # Verify partial static metadata can pass through conversion. Dynamic entries are synthetic.
  for scenario in ['common_only','dynamic_merge','allocator_null']:
   f=Fixture(symbols={'constructCustStaticMetadata_DEVICE_CAMERA_COMMON':{'writes':{0x1a0000:[0x100],0x150000:[0]}}});o=f.configured(sensor,'static');m=f.newmeta();out=f.alloc(bytes(4));c=f.alloc(bytes(4));f.put(c,f.converter())
   if scenario=='dynamic_merge':f.dynamic={0x150000:[9],0xf0001:[123]};f.dng={0xe0003:[7]}
   f.converter_null=scenario=='allocator_null'
   rc=f.run(f.allow('23constructStaticMetadataE'),o,c,out,m)
   assert rc==0 and f.metadata[m][0x1a0000]==[0x100]
   if scenario=='dynamic_merge':assert f.metadata[m][0x150000]==[9] and f.metadata[m][0xe0003]==[7]
   results.append({'sensor':sensor,'path':'construct_static','scenario':scenario,'return':rc,'output_null':f.get(out)==0,'metadata_stub':f.metadata[m],'events':f.events})
  for scenario in ['missing','valid_stub','empty_stub','allocator_null','converter_error']:
   defs={} if scenario=='missing' else {'constructCustRequestMetadata_COMMON':{'writes':{} if scenario=='empty_stub' else {1:[1]}}}
   f=Fixture(symbols=defs);o=f.configured(sensor,'request');f.stubs[0x246ec]='_ZN5NSCam15IMetadataTagSetC1Ev';f.converter_null=scenario=='allocator_null';f.converter_error=int(scenario=='converter_error')
   rc=f.run(f.allow('15TemplateRequest8onCreateE'),o,0);count=len(f.vectors.get(o+0x14,[]))
   assert count==(6 if scenario=='valid_stub' else 0)
   assert rc==(-2 if scenario=='missing' else -2147483648 if scenario=='converter_error' else 0)
   # Missing/empty/allocation failures leave the default fallback pointer null.
   if not count:assert f.run(f.allow('15TemplateRequest7getDataE'),o,1)==0
   results.append({'sensor':sensor,'path':'template_onCreate','scenario':scenario,'return':rc,'cached_templates':count,'events':f.events})
  # Public getInstance returns an object even though onCreate failed.
  f=Fixture();f.sensor_name=sensor;f.obj('request');f.allow('15TemplateRequest8onCreateE');f.allowed.append((0x26fa4,0x27038));obj=f.run(f.allow('16ITemplateRequest11getInstanceE'),0)
  assert obj>0 and not f.vectors.get(obj+0x14,[]) and f.run(f.allow('15TemplateRequest7getDataE'),obj,1)==0
  results.append({'sensor':sensor,'path':'getInstance_after_missing_template','non_null_object':True,'getData_null':True,'events':f.events})
  # Actual halsensor buildStaticInfo: private Info pointer layout, handle-local lookup.
  for scenario,defs in [('missing',{}),('sensor_true',{'constructCustStaticMetadata_DEVICE_SENSOR_'+sensor:{'status':1,'writes':{7:[8]}}}),('sensor_zero',{'constructCustStaticMetadata_DEVICE_SENSOR_'+sensor:{'status':0,'writes':{7:[8]}}})]:
   f=Fixture('lib_libcam.halsensor.so',defs);f.allowed.append((0xdf98,0xe084));info=f.alloc(bytes(16));f.put(info+0xc,f.alloc(sensor.encode()+b'\0'));m=f.newmeta();rc=f.run(f.allow('15buildStaticInfoE'),0,info,m)
   assert rc==1
   look=[e['symbol'] for e in f.events if e['event']=='dlsym'];assert len(look)==(31 if scenario=='sensor_true' else 32)
   assert bool(f.metadata[m])==(scenario!='missing')
   results.append({'sensor':sensor,'path':'halsensor_buildStaticInfo','scenario':scenario,'return':rc,'metadata_stub':f.metadata[m],'events':f.events})
 # Empty getDeviceVersion has no default-HAL3 or HAL1 guard.
 f=Fixture();o=f.configured('SENSOR_DRVNAME_OV5670_MIPI_RAW','static');f.newmeta(o+0x1c)
 try:f.run(f.allow('16getDeviceVersionE'),o)
 except AssertionError as e:
  assert 'missing entry access' in str(e)
  results.append({'path':'getDeviceVersion','scenario':'missing_entry','expected_fault':'unchecked missing entry read caught by stub'})
 else:raise AssertionError('unexpected safe default version')
 # Halsensor lookup helper uses boolean success, while provider uses status_t.
 for scenario,defs,expected in [('missing',{},0),('returns_true',{'test':{'status':1}},1),('returns_zero',{'test':{'status':0}},0)]:
  f=Fixture('lib_libcam.halsensor.so',defs);f.allowed.append((0xdf98,0xe084));s=f.alloc(bytes(4));f.put(s,f.alloc(b'test\0'));rc=f.run(0xdf99,s,f.alloc(bytes(16)),f.newmeta());assert rc==expected
  results.append({'path':'halsensor_lookup','scenario':scenario,'return':rc,'events':f.events})
 # Actual OEM tag registration body: records schema; never supplies sensor values.
 f=Fixture();v=f.alloc(bytes(128));o=f.alloc(bytes(8));f.put(o,v)
 for off in range(0,128,4):f.put(v+off,f.stub('tagset_'+hex(off)))
 f.allowed.append((0xf00c,0x11644));f.run(0xf00d,o)
 (ROOT/'evidence/oem-tag-schema.json').write_text(json.dumps(f.events,indent=2))
 out={'fixture':'actual ARM32 instructions with explicit Python external stubs','native_vendor_execution':False,'limits':{'mapped_bytes':0x600000,'instructions_per_call':50000},'packages':{n:importlib.metadata.version(n) for n in ['unicorn','capstone','pyelftools']},'tests':results,'passed':len(results)}
 (ROOT/'evidence/fixture-results.json').write_text(json.dumps(out,indent=2));print('PASS',len(results))
if __name__=='__main__':main()
