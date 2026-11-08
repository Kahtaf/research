from analyze import *
import shutil,hashlib
W=ROOT.parent
copied=[]
for rel in ['evidence/identification.json','inputs/kd_imgsensor.h','inputs/kd_camera_feature.h']:
 p=W/'2026-11-06-asus-fitted-camera-identification'/rel;q=ROOT/'inputs'/p.name;shutil.copyfile(p,q);copied.append({'source':str(p),'destination':str(q.relative_to(ROOT)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(ROOT/'evidence/parent-source-pins.json').write_text(json.dumps(copied,indent=2))
closure=json.loads((ROOT/'evidence/complete-closure-constructors.json').read_text());schemas=json.loads((ROOT/'evidence/schema-witness.json').read_text())['values']
cat=['LENS','SENSOR','TUNING_3A','FLASHLIGHT','SCALER','FEATURE','CAMERA','REQUEST']
paths=[]
for width in ['lib','lib64']:
 rows=[r for r in closure['rows'] if '/'+width+'/' in r['path']];exports={s:r['path'] for r in rows for s in r.get('metadata_exports',[])}
 for sensor,slot,idnum in [('OV5670',1,0x5670),('OV2680',2,0x2680)]:
  name='SENSOR_DRVNAME_'+sensor+'_MIPI_RAW';look=[]
  for family in ['DEVICE','PROJECT']:
   for category in cat:
    for suffix in [name,'COMMON']:
     symbol=f'constructCustStaticMetadata_{family}_{category}_{suffix}'
     look.append({'symbol':symbol,'origin_in_scanned_default_scope':exports.get(symbol),'family':family,'category':category,'fallback':suffix=='COMMON'})
  req=['constructCustRequestMetadata_'+name,'constructCustRequestMetadata_COMMON']
  paths.append({'width':32 if width=='lib' else 64,'sensor':sensor,'kernel_slot':slot,'role_from_oem_enum':'main' if slot==1 else 'sub','cached_selected_driver':sensor.lower()+'mipiraw','source_model_id':hex(idnum),'id_qualification':'OEM source and ELF registry constants, not a fresh physical numerical chip-ID read','lookup_name':name,'logical_camera_id':None,'facing_qualified':False,'static_lookup_order':look,'halsensor_lookup_order':[x['symbol'] for x in look],'halsensor_scope':'dlopen(libcam.halsensor.so, 2), handle dependency search; selected and COMMON symbols absent there','request_lookup_order':[{'symbol':s,'origin':exports.get(s)} for s in req],'request_missing_status':-2,'templates_attempted_by_onCreate':[1,2,3,4,5,6],'actual_missing_path_stops_at':1,'common_device_version':'0x100','selected_hal3_contract':'NOT_SUPPLIED_BY_INSPECTED_STOCK_MACHINERY','sensor_specific_metadata_constructors_present':False})
functions={}
for w in ['lib','lib64']:
 for n in ['libcam.metadataprovider.so','libcam.halsensor.so','libcam.hal3a.v3.dng.so','libcam.metadata.so']:
  b=Binary(ROOT/'inputs'/(w+'_'+n));functions[w+'_'+n]=[{'symbol':s.name,'address':hex(s['st_value']&~1),'entry':hex(s['st_value']),'size':s['st_size']} for s in b.syms if s['st_info']['type']=='STT_FUNC' and s['st_size'] and re.search('construct|Construct|queryStaticInfo|queryDriverName|MetadataProviderC1|TemplateRequest8onCreate|TemplateRequest7getData|ITemplateRequest11getInstance|buildStaticInfo|buildSensorMetadata|getDeviceVersion|DngInfoImp17getStatic|IMetadataC1Ev|IMetadata11ImplementorC1Ev',s.name)]
required=[]
for n,v in schemas.items():
 if n in ['ANDROID_INFO_SUPPORTED_HARDWARE_LEVEL_LIMITED','ANDROID_INFO_SUPPORTED_HARDWARE_LEVEL_LEGACY','ANDROID_LOGICAL_MULTI_CAMERA_PHYSICAL_IDS']:continue
 required.append({'sdk37_tag':n,'value':v['hex'],'status':'COMMON supplies an unqualified generic value' if n in ['ANDROID_INFO_SUPPORTED_HARDWARE_LEVEL','ANDROID_SENSOR_ORIENTATION','ANDROID_LENS_FACING'] else 'selected usable contract absent/unqualified','requirement':'Minimum contract candidates, capability/hardware-level dependent where applicable; not a complete CTS list'})
m={'question':'Selected OV5670/OV2680 OEM HAL3 static/default-request contract','conclusion':'No complete supported HAL3 contract supplied by inspected stock dispatch. Sensor-specific constructors absent; COMMON selects HAL1; default requests fail. Hardware feasibility is not disproved.','paths':paths,'functions':functions,'required_entries':required,'scope':{'stock_elfs_scanned':sum(not r.get('absent') for r in closure['rows']),'unresolved_needed':closure['unresolved_needed'],'runtime_injected_namespace_qualified':False},'dynamic_sources':{'IHalSensorList_queryStaticInfo':'EnumInfo metadata built through handle-scoped constructors; missing paths still return true with empty metadata','gSensorMetadata':'Separate driver-populated global with sensor facts/scenario package; no merge into selected EnumInfo on traced buildStaticInfo path','DngInfo':'NVRAM-backed illuminants/matrices only; constructor/read not run; cannot provide request/stream/capability contract','IMetadata_default':'Empty entry-vector container, not selected-sensor defaults','request_updateData':'After successful constructor only; derives crop from static active array, not a missing-template fallback'},'independent_unresolved':['GraphicBuffer OEM 136 vs SDK37 1784-byte ARM32 layout','PropertyMap old KeyedVector ABI','19 external closure symbols from prior audit','native/compat ioctl translations','real pipeline/frame/hardware qualification'],'first_ram_kernel_probe_blocked_by_this':False,'fixture_cases':{'arm32':107,'arm64':68},'next_boundary':'Isolated source metadata contract for exact OV5670/OV2680 modes and MT8163 ISP/control pipeline, with provenance for every stream/timing/control and truthful templates; no product enable/version override until it and hardware are qualified'}
(ROOT/'evidence/mapping.json').write_text(json.dumps(m,indent=2))
# Narrow extra disassembly, including compiler-hidden bodies and real registry initialization.
for w,n,a,size in [('lib','libcameracustom.so',0xb35b1,0x1a8),('lib64','libcam.halsensor.so',0x108ac,0x150)]:
 b=Binary(ROOT/'inputs'/(w+'_'+n));(ROOT/'evidence'/(w+'_selected-hidden.txt')).write_text(b.dis({'name':'bounded_hidden_body','st_value':a,'st_size':size}))
b=Binary(ROOT/'inputs/lib64_libcam.metadataprovider.so');(ROOT/'evidence/lib64_common.txt').write_text(b.dis(b.names['constructCustStaticMetadata_DEVICE_CAMERA_COMMON']))
# Pin all authored/copy evidence, excluding derived manifest itself and disposable environment/cache.
pins=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_file() and 'venv' not in p.parts and '__pycache__' not in p.parts and p.name!='artifact-pins.json':pins.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'evidence/artifact-pins.json').write_text(json.dumps(pins,indent=2));print('mapping paths',len(paths),'pinned artifacts',len(pins))
