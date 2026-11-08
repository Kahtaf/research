import sys
sys.dont_write_bytecode = True
from pathlib import Path
import re,json,importlib.util,base64,hashlib
r=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('remote',r.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
files={}
for label,path,values in [
 ('oem','fixture/oem-kernel/drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define.h',[3040,3080,3090]),
 ('kernel49','fixture/sdk37/kernel/asus/p00a-fd/drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define_default.h',[3041,3081,3092])]:
 text=(r/path).read_text();start=text.index('SENSOR_FEATURE_BEGIN');end=text.index('}',start)
 body=text[start:end]
 src='#include <stdint.h>\n#define SENSOR_FEATURE_START 3000\nenum {\n'+body+'};\n'
 names=['SENSOR_FEATURE_CHECK_SENSOR_ID','SENSOR_FEATURE_GET_CROP_INFO','SENSOR_FEATURE_SET_ISO']
 for name,value in zip(names,values):src+=f'_Static_assert({name} == {value}, "feature ABI mismatch");\n'
 src+='const uint32_t feature_ids[] = {'+', '.join(names)+'};\n'
 dest=r/'fixture'/('enum_'+label+'.c');dest.write_text(src);files[dest.name]=src
script='payload='+repr(files)+'\n'+r'''
from pathlib import Path
import os,resource,subprocess,json,base64,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-source-abi-route');out=r/'abi-out'
receipts=json.loads((out/'compile.json').read_text());compile=next(x for x in receipts if '-c' in x['argv']);rows=[]
for name,source in payload.items():
 p=r/name;p.write_text(source);args=list(compile['argv']);args[args.index('-c')+1]=str(p);args[args.index('-o')+1]=str(out/(p.stem+'.o'))
 run=subprocess.run(args,cwd=compile['cwd'],capture_output=True,text=True,timeout=45);rows.append(dict(argv=args,cwd=compile['cwd'],returncode=run.returncode,stderr=run.stderr));assert run.returncode==0,run.stderr
artifacts={}
for name in ['libp00a_camera_abi_probe.so','camera_abi_probe.o','enum_oem.o','enum_kernel49.o','input-pins.json','compile.json']:
 data=(out/name).read_bytes();assert len(data)<1024**2;artifacts[name]={'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()}
print(json.dumps({'enum_compiles':rows,'artifacts':artifacts}))
'''
data=json.loads(m.run(script));(r/'evidence/enum-compiles.json').write_text(json.dumps(data['enum_compiles'],indent=2)+'\n');pins=[]
for name,info in data['artifacts'].items():
 raw=base64.b64decode(info['base64']);assert hashlib.sha256(raw).hexdigest()==info['sha256'];dest=r/('evidence' if name.endswith('.json') else 'fixture')/name;dest.write_bytes(raw);pins.append({'path':str(dest.relative_to(r)),'sha256':info['sha256'],'bytes':len(raw)})
(r/'evidence/compile-artifacts.json').write_text(json.dumps(pins,indent=2)+'\n');print('PASS two ARM64 enum compilations against frozen SDK37 includes; 6 small outputs retrieved; no target execution')
