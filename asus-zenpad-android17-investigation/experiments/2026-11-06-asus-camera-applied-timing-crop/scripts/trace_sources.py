"""Pin local public transport sources and record exact unexecuted boundaries."""
import json
import re
import subprocess
from pathlib import Path
from extract import SPIKE, ROOT, PARENT, function, masked, block, receipt, sha, dump

OEM=ROOT/'2026-11-05-asus-latest-android-feasibility/sources/asus-original'
KERNEL=OEM/'kernel-3.18'
REL='drivers/misc/mediatek/'
SOURCES={
 'sensor_dispatch':KERNEL/REL/'imgsensor/src/mt8163/kd_sensorlist.c',
 'sensor_ioctl':KERNEL/REL/'imgsensor/inc/kd_imgsensor.h',
 'sensor_abi':KERNEL/REL/'imgsensor/inc/kd_imgsensor_define.h',
 'scalar_types':KERNEL/REL/'imgsensor/inc/kd_camera_typedef.h',
 'isp_dispatch':KERNEL/REL/'cameraisp/src/mt8163/camera_isp.c',
 'isp_abi':KERNEL/REL/'cameraisp/src/mt8163/inc/camera_isp.h',
 'isp_build':KERNEL/REL/'cameraisp/src/mt8163/Makefile',
}


def named_function(text,name):
    pattern=r'^(?:(?:static|inline)\s+)*(?:\w+)\s+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{'
    matches=list(re.finditer(pattern,masked(text),re.M));assert len(matches)==1,(name,len(matches))
    return block(text,matches[0].start())


def main():
    pins=json.loads((SPIKE/'inputs/public-transport-pins.json').read_text())
    result={'scope':'local public OEM source; text receipts only; no transport/ISP function compiled or run','pins':pins,'functions':{},'snippets':{},'sensor_features':{}}
    texts={}
    for key,path in SOURCES.items():
        raw=path.read_bytes();pin=pins[key];assert sha(raw)==pin['sha256'] and str(path.relative_to(ROOT))==pin['source']
        texts[key]=raw.decode();(SPIKE/'inputs'/path.name).write_bytes(raw)
    functions={'sensor_dispatch':['adopt_CAMERA_HW_FeatureControl','kd_MultiSensorFeatureControl','kd_MultiSensorGetInfo','adopt_CAMERA_HW_GetInfo','adopt_CAMERA_HW_GetInfo2','compat_get_acdk_sensor_featurecontrol_struct'],
               'isp_dispatch':['ISP_WriteReg','ISP_WriteRegToHw']}
    # Some public release names differ; discovered spelling must match exactly.
    for key,names in functions.items():
        text=texts[key];source=pins[key]['source']
        for name in names:
            span=named_function(text,name);body=text[slice(*span)];ref=receipt(text,span,source)
            result['functions'][name]=ref;(SPIKE/'generated'/f'text-only-{name}.txt').write_text(body)
    def snippet(key,name,start,end):
        text=texts[key];a=text.index(start);b=text.index(end,a)+len(end);span=(a,b)
        result['snippets'][name]=receipt(text,span,pins[key]['source'])
        (SPIKE/'generated'/f'text-only-{name}.txt').write_text(text[a:b])
    snippet('sensor_abi','feature_envelope','typedef struct {\n\tCAMERA_DUAL_CAMERA_SENSOR_ENUM InvokeCamera;\n\tACDK_SENSOR_FEATURE_ENUM FeatureId;','} ACDK_SENSOR_FEATURECONTROL_STRUCT, *PACDK_SENSOR_FEATURECONTROL_STRUCT;')
    snippet('sensor_abi','winsize_type','typedef struct {\n\tMUINT16 full_w;','} SENSOR_WINSIZE_INFO_STRUCT;')
    snippet('isp_abi','isp_register_abi','typedef struct {\n\tunsigned int Addr;','} ISP_REG_IO_STRUCT;')
    snippet('isp_dispatch','isp_ioctl_write','case ISP_WRITE_REGISTER:','case ISP_HOLD_REG_TIME:')
    snippet('sensor_dispatch','sensor_ioctl_feature','case KDIMGSENSORIOC_X_FEATURECONCTROL:','break;')
    snippet('sensor_dispatch','getinfo_grab_export','SensorInfo.SensorGrabStartX_PRV =','SensorInfo.SensorGrabStartY_VD2 = pInfo4[IDNum]->SensorGrabStartY;')
    for sensor in ['ov5670','ov2680']:
        x=json.loads((SPIKE/'evidence/extraction.json').read_text())['sensors'][sensor];source=x['source']['path'];text=(ROOT/source).read_text()
        for name in ['get_info','get_resolution']:
            span=function(text,name);result['functions'][sensor+'-'+name]=receipt(text,span,source)
            (SPIKE/'generated'/f'text-only-{sensor}-{name}.txt').write_text(text[slice(*span)])
        a,b=function(text,'feature_control');body=text[a:b]
        (SPIKE/'generated'/f'text-only-{sensor}-feature_control.txt').write_text(body)
        result['sensor_features'][sensor]={'full_feature_control_receipt':receipt(text,(a,b),source),
          'handled_cases':re.findall(r'case\s+(SENSOR_FEATURE_\w+)\s*:',masked(body)),
          'not_handled':['SENSOR_FEATURE_SET_SHUTTER_FRAME_TIME','SENSOR_FEATURE_SET_TARGET_FRAME_RATE','SENSOR_FEATURE_SET_MIN_MAX_FPS'],
          'entry_word_declarations':[line.strip() for line in body.splitlines() if re.search(r'\*feature_(?:data|return)',line) and '=' in line and 'feature_para' in line],
          'crop_pointer_expression':'(SENSOR_WINSIZE_INFO_STRUCT *)(uintptr_t)(*(feature_data+1))',
          'crop_bytes':32,'transport_pointer_safety_qualified':False}
        assert not set(result['sensor_features'][sensor]['not_handled'])&set(result['sensor_features'][sensor]['handled_cases'])
    inventory=[]
    for area in ['hardware','vendor']:
        p=subprocess.run(['rg','--files',str(OEM/area)],capture_output=True,text=True,check=True)
        paths=p.stdout.splitlines();matches=[str(Path(x).relative_to(OEM)) for x in paths if re.search(r'(?i)(mtkcam|sensorhal|ihalsensor|imgsensor_drv|camera|ispdrv|cropper)',x)]
        # Exact feature/grab references; public source only, no binary loading.
        q=subprocess.run(['rg','-l','GET_CROP_INFO|SensorGrabStartX|SET_MAX_FRAME_RATE_BY_SCENARIO',str(OEM/area),'--glob','*.[ch]','--glob','*.cpp'],capture_output=True,text=True)
        assert q.returncode in [0,1]
        inventory.append({'area':str((OEM/area).relative_to(ROOT)),'file_count':len(paths),'path_pattern':'mtkcam|sensorhal|ihalsensor|imgsensor_drv|camera|ispdrv|cropper','path_matches':matches,
          'content_pattern':'GET_CROP_INFO|SensorGrabStartX|SET_MAX_FRAME_RATE_BY_SCENARIO','content_matches':[str(Path(x).relative_to(ROOT)) for x in q.stdout.splitlines()]})
    result['local_search']=inventory
    result['boundaries']={
      'request_to_sensor':{'last_public_entry':'adopt_CAMERA_HW_FeatureControl(ACDK_SENSOR_FEATURECONTROL_STRUCT*) -> kd_MultiSensorFeatureControl -> selected feature_control',
         'missing':'Fitted MT8163 userspace caller/3A implementation that translates Android request frame-duration/exposure units into scenario-rate and 64-bit shutter words, schedules their order and accounts for application/result latency. No public caller name available in inspected release; no invented proprietary symbol.',
         'hazards':['Selected SET_ESHUTTER consumes 8-byte unsigned long long then narrows to kal_uint16; kernel SET_SENSOR_SYNC path passes FeatureParaLen=2 and address of u2SensorNewExpTime. Incompatible read extent is not a validated payload ABI.',
                    'GET_PERIOD reports software uint16 line/frame values, not actual register state or timestamped applied frame duration.',
                    'SET_SHUTTER_FRAME_TIME enum exists in header but selected feature_control handles none; default returns ERROR_NONE without applying it.']},
      'crop_to_isp':{'last_sensor_outputs':['SENSOR_WINSIZE_INFO_STRUCT (16 uint16 fields)','get_info scenario SensorGrabStartX/Y','get_resolution grab dimensions'],
         'next_public_entry':'ISP_WRITE_REGISTER -> ISP_WriteReg(ISP_REG_IO_STRUCT*) -> optional held list or ISP_WriteRegToHw(ISP_REG_STRUCT*, Count)',
         'missing':'The userspace MT8163 ISP/sensor-HAL crop/scale builder between these endpoints: its exact callable source or ABI, input coordinate units/origins, Bayer alignment and rounding/clipping, TG/grab offsets, sensor mirror/binning association, output register-list fields and frame-application ordering.',
         'crop_pointer_hazard':'GET_CROP_INFO interprets feature word1 as a kernel-dereferenceable destination; inspected generic feature ioctl copies only the flat payload and shows no nested crop destination marshalling. compat helper translates envelope pointers only. Do not use host pointer success as external ioctl proof.',
         'transform':None,'inference':'The inspected ISP write endpoint forwards caller Addr/Val lists; this body does not construct a sensor winsize/grab-to-ISP transform. This does not assert no transform exists elsewhere in unavailable vendor code.'}}
    dump(SPIKE/'evidence/public-path-boundaries.json',result)

if __name__=='__main__':main()
