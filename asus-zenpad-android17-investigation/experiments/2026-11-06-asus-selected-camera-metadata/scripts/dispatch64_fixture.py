"""AArch64 counterpart: only dispatch/lookup instructions; all externals stubbed."""
from analyze import Binary,ROOT
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
import json
class Fixture64:
 def __init__(self,defs):
  self.b=Binary(ROOT/'inputs/lib64_libcam.metadataprovider.so');self.u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);self.u.mem_map(0,0x600000)
  for s in self.b.e.iter_segments():
   if s['p_type']=='PT_LOAD':self.u.mem_write(s['p_vaddr'],s.data())
  self.heap=0x100000;self.callbacks=0x500000;self.stubs={};self.allowed=[];self.defs=defs;self.events=[];self.meta={}
  plt=self.b.e.get_section_by_name('.plt')['sh_addr']+32
  for i,r in enumerate(self.b.e.get_section_by_name('.rela.plt').iter_relocations()):self.stubs[plt+i*16]=self.b.syms[r['r_info_sym']].name
  for a,(name,addend) in self.b.rel.items():
   if name=='__stack_chk_guard':self.put(a,self.alloc(bytes.fromhex('1234567887654321')))
  self.stop=0x5ff000;self.u.hook_add(UC_HOOK_CODE,self.hook)
 def get(self,a):return int.from_bytes(self.u.mem_read(a,8),'little')
 def put(self,a,v):self.u.mem_write(a,(v&0xffffffffffffffff).to_bytes(8,'little'))
 def alloc(self,data):a=self.heap;self.heap+=(len(data)+15)&~15;self.u.mem_write(a,data);return a
 def string(self,a):return bytes(self.u.mem_read(a,512)).split(b'\0')[0].decode()
 def stub(self,name):a=self.callbacks;self.callbacks+=4;self.stubs[a]=name;return a
 def allow(self,part):
  ss=[s for s in self.b.syms if part in s.name and s['st_size']];assert len(ss)==1;v=ss[0]['st_value'];self.allowed.append((v,v+ss[0]['st_size']));return v
 def ret(self,v=0):self.u.reg_write(UC_ARM64_REG_X0,v&0xffffffffffffffff);self.u.reg_write(UC_ARM64_REG_PC,self.u.reg_read(UC_ARM64_REG_LR))
 def hook(self,u,a,size,_):
  if a==self.stop:u.emu_stop();return
  if a in self.stubs:
   n=self.stubs[a];r=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(8)]
   if n=='_ZN7android7String86formatEPKcz':
    fmt=self.string(r[0]);args=[self.string(x) for x in r[1:1+fmt.count('%s')]];self.put(u.reg_read(UC_ARM64_REG_X8),self.alloc((fmt%tuple(args)).encode()+b'\0'));self.ret();return
   if n=='dlsym':
    name=self.string(r[1]);self.events.append({'event':'dlsym','handle':hex(r[0]),'symbol':name});self.ret(self.stub('constructor:'+name) if name in self.defs else 0);return
   if n.startswith('constructor:'):
    name=n.split(':',1)[1];s=self.defs[name];self.meta.update(s.get('writes',{}));self.events.append({'event':'constructor_stub','symbol':name,'second_arg':r[1],'status':s.get('status',0)});self.ret(s.get('status',0));return
   if n in ['_ZN7android7String8D1Ev','__android_log_print']:self.ret();return
   if n=='strerror':self.ret(self.alloc(b'stub error\0'));return
   raise AssertionError(('unstubbed',n,hex(a)))
  assert any(lo<=a<hi for lo,hi in self.allowed),('outside whitelist',hex(a))
 def run(self,sensor,kind,template=1):
  o=self.alloc(bytes(128));v=self.alloc(bytes(256));m=self.alloc(bytes(16));self.put(o,v)
  if kind=='static':
   self.put(o+0x20,self.alloc(sensor.encode()+b'\0'));self.put(v+0x78,self.allow('40impConstructStaticMetadata_by_SymbolNameE'));pc=self.allow('26impConstructStaticMetadataE')
  else:
   self.put(o+0x18,self.alloc(sensor.encode()+b'\0'));self.put(v+0x50,self.allow('41impConstructRequestMetadata_by_SymbolNameE'));pc=self.allow('27impConstructRequestMetadataE')
  for reg,x in [(UC_ARM64_REG_X0,o),(UC_ARM64_REG_X1,m),(UC_ARM64_REG_X2,template),(UC_ARM64_REG_SP,0x3ff000),(UC_ARM64_REG_LR,self.stop)]:self.u.reg_write(reg,x)
  self.u.emu_start(pc,self.stop,count=50000);assert self.u.reg_read(UC_ARM64_REG_PC)==self.stop
  v=self.u.reg_read(UC_ARM64_REG_W0);return v if v<0x80000000 else v-0x100000000

def main():
 rows=[];cats=['LENS','SENSOR','TUNING_3A','FLASHLIGHT','SCALER','FEATURE','CAMERA','REQUEST']
 for sensor in ['SENSOR_DRVNAME_OV5670_MIPI_RAW','SENSOR_DRVNAME_OV2680_MIPI_RAW']:
  for scenario,defs in [('missing',{}),('common_only',{'constructCustStaticMetadata_DEVICE_CAMERA_COMMON':{'writes':{0x1a0000:[0x100]}}}),('sensor_present',{'constructCustStaticMetadata_DEVICE_SENSOR_'+sensor:{}}),('sensor_errors',{'constructCustStaticMetadata_DEVICE_SENSOR_'+sensor:{'status':-22},'constructCustStaticMetadata_DEVICE_SENSOR_COMMON':{'status':-5}})]:
   f=Fixture64(defs);rc=f.run(sensor,'static');assert rc==0;expected=[]
   for family in ['DEVICE','PROJECT']:
    for cat in cats:
     n=f'constructCustStaticMetadata_{family}_{cat}_{sensor}';expected.append(n)
     if n not in defs or defs[n].get('status',0):expected.append(f'constructCustStaticMetadata_{family}_{cat}_COMMON')
   assert [e['symbol'] for e in f.events if e['event']=='dlsym']==expected
   rows.append({'sensor':sensor,'path':'static','scenario':scenario,'return':rc,'events':f.events})
  for scenario,defs,expect in [('missing',{},-2),('sensor_present',{'constructCustRequestMetadata_'+sensor:{}},0),('common_present',{'constructCustRequestMetadata_COMMON':{}},0),('sensor_error_common_missing',{'constructCustRequestMetadata_'+sensor:{'status':-22}},-2),('sensor_error_common_error',{'constructCustRequestMetadata_'+sensor:{'status':-22},'constructCustRequestMetadata_COMMON':{'status':-5}},-5)]:
   for t in range(1,7):
    f=Fixture64(defs);rc=f.run(sensor,'request',t);assert rc==expect;rows.append({'sensor':sensor,'path':'request','scenario':scenario,'template':t,'return':rc,'events':f.events})
 (ROOT/'evidence/fixture64-results.json').write_text(json.dumps({'fixture':'Actual AArch64 dispatch instructions; externals/constructors stubbed','native_vendor_execution':False,'passed':len(rows),'tests':rows},indent=2));print('PASS',len(rows))
if __name__=='__main__':main()
