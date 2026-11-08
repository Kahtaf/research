#!/usr/bin/env python3
"""Offline public-evidence consistency checks; never contacts a device or builder."""
from pathlib import Path
import json,hashlib,datetime
p=Path(__file__).resolve().parents[1];base=p.parent
checks=[]
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)
def first_json(name):return json.JSONDecoder().raw_decode((p/'evidence'/name).read_text())[0]
n=first_json('nvram-tables.txt');rows=n['lib']['rows'];by={r['path']:r for r in rows}
check('ARM32 and ARM64 public NVRAM table metadata agree',rows==n['lib64']['rows'])
check('49 common plus 22 custom records; contiguous unique indices',len(rows)==71 and [r['lid_candidate'] for r in rows]==list(range(71)) and len(by)==71)
for suffix,lid,size in [('APCFG/APRDEB/BT_Addr',1,64),('APCFG/APRDEB/WIFI',53,512),('APCFG/APRDCL/HWMON_ACC',12,12),('APCFG/APRDCL/HWMON_PS',18,12),('media/Audio_Buffer_DC_Calibration_Param',65,8)]:
 r=by['/data/nvram/'+suffix];check('Public table '+suffix,r['lid_candidate']==lid and r['payload_bytes']==size)
prod=first_json('product-snapshot.json')
for name,t in prod['trees'].items():
 check(name+' tree inspected',t['exists'])
 check(name+' has no audio/camera/sensors manifest declarations',not any(x.startswith(('android.hardware.audio','android.hardware.camera','android.hardware.sensors')) for x in t['hal_names']))
 check(name+' has no device make inclusion for audio/camera/sensors HALs',not any(any(x in l for x in ['android.hardware.audio','android.hardware.camera','android.hardware.sensors','audio.primary.mt8163','camera.mt8163','sensors.mt8163']) for l in t['make_lines']))
config=(base/'2026-11-06-asus-combined-kernel-integration/artifacts/handoff-r5/resolved.config').read_text()
for c in ['CONFIG_MTK_IMGSENSOR','CONFIG_CUSTOM_KERNEL_ACCELEROMETER','CONFIG_CUSTOM_KERNEL_MAGNETOMETER','CONFIG_CUSTOM_KERNEL_ALSPS']:
 check(c+' disabled in physical combined config',f'# {c} is not set' in config)
for c in ['CONFIG_TOUCHSCREEN_GOODIX','CONFIG_KEYBOARD_MTK','CONFIG_SND_SOC_MT8163','CONFIG_SUSPEND']:
 check(c+' enabled',f'{c}=y' in config)
source=(p/'evidence/details-r2.txt').read_text()
check('SDK37 explicitly rejects camera HAL1', 'ERROR_DEPRECATED_HAL' in source and 'HAL version %d no longer supported' in source)
iface=(p/'evidence/interface-audit.txt').read_text()
check('Two sensor event ABI implementations identified','input_report_abs' in iface and 'sensor_event_read' in iface)
stock=first_json('stock-elf-and-config.txt')
for arch in ['lib','lib64']:
 for module in ['audio.primary.mt8163.so','camera.mt8163.so','sensors.mt8163.so']:
  check(arch+'/'+module+' public ELF inspected',any(r['path']=='/vendor/'+arch+'/hw/'+module for r in stock))
# Export metadata only: none of these rows contain actual calibration contents.
metadata={'source':'Public WW-5.3.20.0 libcustom_nvram.so, both architectures','id_interpretation':'common index 0..48; custom LID=49+index; corroborated by ARM64 libnvram NVM_GetCfgFileTable/GetFileDesc/GetLIDByName disassembly and GOT relocations','limits':'Static payload sizes, NOT file-container lengths; preserve whole existing files including checksums; actual unit existence and values never inspected','records':[{**{k:v for k,v in r.items() if k!='lid_candidate'},'stock_lid':r['lid_candidate']} for r in rows]}
(p/'report/calibration-records.json').write_text(json.dumps(metadata,indent=2)+'\n')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':len(checks),'checks':checks,'physical_tests':0,'compile_tests':0,'scope':'Public ELF/static source consistency only; no runtime or backup-completeness qualification'}
(p/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':len(checks),'physical_tests':0,'compile_tests':0}))
