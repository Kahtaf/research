from pathlib import Path
import re,json,hashlib
r=Path(__file__).resolve().parents[1]
s=(r/'evidence/metadata-edges.txt').read_text();chunks=s.split('SOURCE ')
for c in chunks[1:]:
 lines=c.splitlines();path=lines[0]
 if len(lines)<2 or not lines[1].startswith('SHA256 '):continue
 text='\n'.join(lines[2:]).split('\nCLANG ')[0].rstrip()+'\n'
 dest=r/'fixture/sdk37'/path.split('/srv/android/lineage24/',1)[1];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
def strip(s):return re.sub(r'//[^\n]*','',re.sub(r'/\*.*?\*/','',s,flags=re.S))
def features(s):
 s=strip(s);start=s.index('SENSOR_FEATURE_BEGIN');end=s.index('}',start);out={};i=3000
 for item in s[start:end].split(','):
  item=item.strip()
  if not item:continue
  parts=item.split('=');name=parts[0].strip()
  if len(parts)>1:
   v=parts[1].strip();i=3000 if v=='SENSOR_FEATURE_START' else int(v,0)
  out[name]=i;i+=1
 return out
old=(r/'fixture/oem-kernel/drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define.h').read_text()
new=(r/'fixture/sdk37/kernel/asus/p00a-fd/drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define_default.h').read_text()
a,b=features(old),features(new)
res={'old_count':len(a),'new_count':len(b),'changed':[{'name':k,'oem':v,'kernel49':b.get(k)} for k,v in a.items() if b.get(k)!=v],'new_only':{k:v for k,v in b.items() if k not in a},'selected':{k:{'oem':a.get(k),'kernel49':b.get(k)} for k in ['SENSOR_FEATURE_CHECK_SENSOR_ID','SENSOR_FEATURE_SET_ESHUTTER','SENSOR_FEATURE_SET_GAIN','SENSOR_FEATURE_GET_DEFAULT_FRAME_RATE_BY_SCENARIO','SENSOR_FEATURE_GET_CROP_INFO','SENSOR_FEATURE_SET_ISO']}}
(r/'evidence/sensor-feature-enums.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
