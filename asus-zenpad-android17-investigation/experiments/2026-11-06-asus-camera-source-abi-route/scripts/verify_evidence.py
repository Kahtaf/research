#!/usr/bin/env python3
"""Offline evidence consistency only; never connects to or loads a camera."""
from pathlib import Path
import hashlib,json,struct,re
r=Path(__file__).resolve().parents[1];checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for manifest,base in [('sdk37-source-pins.json',r/'fixture/sdk37'),('source-edge-pins.json',r/'fixture/sdk37')]:
 for item in json.loads((r/'evidence'/manifest).read_text()):check('source '+item['path'],sha(base/item['path'])==item['sha256'])
for item in json.loads((r/'donors/pins.json').read_text()):check('donor '+item['path'],sha(r/'donors'/item['path'])==item['sha256'])
for item in json.loads((r/'evidence/compile-artifacts.json').read_text()):check('compiled artifact '+item['path'],sha(r/item['path'])==item['sha256'])
for i,c in enumerate(json.loads((r/'evidence/compile.json').read_text())):check('ABI compile command '+str(i),c['returncode']==0)
for i,c in enumerate(json.loads((r/'evidence/enum-compiles.json').read_text())):check('enum compile command '+str(i),c['returncode']==0)
d=(r/'fixture/libp00a_camera_abi_probe.so').read_bytes();check('ARM64 ABI ELF',d[:5]==b'\x7fELF\x02' and struct.unpack_from('<H',d,18)[0]==183)
shoff=struct.unpack_from('<Q',d,40)[0];sz,num,sti=struct.unpack_from('<HHH',d,58);sections=[struct.unpack_from('<IIQQQQIIQQ',d,shoff+i*sz) for i in range(num)];strsec=sections[sti];strings=d[strsec[4]:strsec[4]+strsec[5]]
ro=next(s for s in sections if strings[s[0]:].split(b'\0')[0]==b'.rodata');values=struct.unpack('<35I',d[ro[4]:ro[4]+140])
check('compiled C ABI dimensions and offsets',values==(248,120,344,48,4,32,248,256,264,272,280,288,296,136,120,184,136,120,128,128,0,8,24,32,48,56,96,32,32,64,64,32,0x203,0x100,0x302))
check('real metadata API linked',b'validate_camera_metadata_structure' in d and b'libcamera_metadata.so' in d)
check('no camera loader in witness',b'hw_get_module' not in d and b'dlopen' not in d)
a=json.loads((r/'evidence/dependency-audit.json').read_text());check('64 vendor ELF closure records',len(a['vendor_libraries'])==64);check('bounded vendor bytes',a['vendor_total_bytes_read']==22886792)
check('actual module SHA',a['vendor_libraries']['hw/camera.mt8163.so']['sha256']=='2828cc2b636cc038b98422fd68131683921af35c640cbfc8db9ca8caaac7e660')
e=json.loads((r/'evidence/sensor-feature-enums.json').read_text());check('sensor feature mismatch',e['selected']['SENSOR_FEATURE_CHECK_SENSOR_ID']=={'oem':3040,'kernel49':3041});check('not a constant feature shift',e['selected']['SENSOR_FEATURE_SET_ISO']=={'oem':3090,'kernel49':3092})
s=(r/'fixture/sdk37/frameworks/av/services/camera/libcameraservice/CameraService.cpp').read_text();check('HAL1 rejected', 'ERROR_DEPRECATED_HAL' in s)
s=(r/'fixture/sdk37/frameworks/av/services/camera/libcameraservice/common/CameraProviderManager.cpp').read_text();check('earlier HIDL major gate', 'Unsupported HIDL device HAL major version' in s)
check('OEM real factory export','PlatformEntry::createCam3Device' in (r/'evidence/oem-dispatch.txt').read_text())
check('compiled snapshots only',not (r/'fixture/sdk37/frameworks/av/services/camera/libcameraservice/api1/CameraClient.cpp').exists())
for p in [r/'README.md',*list((r/'report').glob('*.md'))]:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if link.startswith(('http:','https:','#')) or link=='evidence/verification.json':continue
  check('document link '+str(p.relative_to(r))+': '+link,(p.parent/link.split('#')[0]).exists())
result={'status':'PASS','checks':len(checks),'scope':'offline hashes, sources, ELF layout and compilation receipts only; no target runtime, camera or physical tests','results':checks};(r/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
