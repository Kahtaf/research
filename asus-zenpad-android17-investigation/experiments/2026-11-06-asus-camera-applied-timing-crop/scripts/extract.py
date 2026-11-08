"""Extract only audited pure arithmetic/write-recording bodies. Full dispatch stays text."""
import json
import re
from pathlib import Path
from parent_extract_helpers import masked, block, function, receipt, sha, dump

SPIKE = Path(__file__).resolve().parents[1]
ROOT = SPIKE.parent
PARENT = ROOT / '2026-11-06-asus-camera-register-witness'
PINS = ROOT / '2026-11-06-asus-camera-metadata-source-inputs/evidence/asus-sensor-source-pins.json'
FUNCTIONS = ['set_dummy', 'set_max_framerate', 'set_max_framerate_by_scenario', 'set_video_mode', 'set_shutter']
FEATURES = ['SET_ESHUTTER', 'SET_MAX_FRAME_RATE_BY_SCENARIO', 'SET_FRAMERATE', 'SET_VIDEO_MODE', 'GET_PERIOD']


def fragment(text, span, source, name, sensor):
    ref = receipt(text, span, source)
    body = text[slice(*span)]
    (SPIKE / 'generated' / f'{sensor}-{name}.inc').write_text(body)
    return body, ref, f'#line {ref["start_line"]} "{source}"\n{body}\n'


def validate():
    for relative, expected in json.loads((SPIKE/'inputs/parent-evidence-pins.json').read_text()).items():
        assert sha((ROOT/relative).read_bytes())==expected, f'Accepted parent input changed: {relative}'
    pins = json.loads(PINS.read_text())['files']
    accepted = json.loads((PARENT / 'evidence/exact-source-receipts.json').read_text())
    assert pins == accepted['four_original_files'] and len(pins) == 4
    for pin in pins:
        raw = (ROOT / pin['path']).read_bytes()
        assert sha(raw) == pin['sha256'] and len(raw) == pin['bytes']
    return pins


def main():
    pins = validate()
    parent_extract = json.loads((PARENT / 'evidence/extraction.json').read_text())
    facts = json.loads((PARENT / 'evidence/sensor-facts.json').read_text())
    acceptance = json.loads((PARENT / 'evidence/parent-source-acceptance.json').read_text())
    assert acceptance['all_functions_exact'] and acceptance['original_source_hashes_verified'] == 4
    consumed = ['README.md', 'report/REPORT.md', 'evidence/sensor-facts.json', 'evidence/exact-source-receipts.json',
                'evidence/metadata-input-coverage.json', 'evidence/parent-source-acceptance.json', 'evidence/extraction.json',
                'evidence/ov5670-traces.json', 'evidence/ov2680-traces.json']
    inherited = {str((PARENT / p).relative_to(ROOT)): sha((PARENT / p).read_bytes()) for p in consumed}
    dump(SPIKE / 'evidence/parent-inputs.json', {'hashes': inherited, 'accepted': acceptance['decision'],
         'previous_counts': {'functions':34,'cases':93,'tests':12}, 'mode_tests_repeated':False})
    result = {'pins':pins, 'pin_manifest_sha256':sha(PINS.read_bytes()), 'sensors':{}}
    support = next(x for x in json.loads((PARENT / 'evidence/exact-source-receipts.json').read_text())['supporting_sources'] if 'winsize_type' in x)
    header = (ROOT / support['source']).read_text(); assert sha(header.encode()) == support['sha256']
    (SPIKE / 'inputs/kd_imgsensor_define.h').write_text(header)
    wt = support['winsize_type']; lines = header.splitlines(keepends=True)
    win_type = ''.join(lines[wt['start_line']-1:wt['end_line']]); assert sha(win_type.rstrip('\n').encode()) == wt['sha256']
    (SPIKE / 'inputs/COPYING.kernel').write_bytes((PARENT / 'inputs/COPYING.kernel').read_bytes())
    for sensor in ['ov5670','ov2680']:
        cp = next(p for p in pins if sensor in Path(p['path']).name and p['path'].endswith('.c'))
        hp = next(p for p in pins if sensor in Path(p['path']).name and p['path'].endswith('.h'))
        source=cp['path']; text=(ROOT/source).read_text(); htext=(ROOT/hp['path']).read_text()
        for p in [cp,hp]:(SPIKE/'inputs'/Path(p['path']).name).write_bytes((ROOT/p['path']).read_bytes())
        names=FUNCTIONS.copy()
        if sensor=='ov5670':names.insert(-1,'write_shutter')
        allow=set(names)|{'write_cmos_sensor','spin_lock','spin_unlock','spin_lock_irqsave','spin_unlock_irqrestore','LOG_INF'}
        pieces=[]; refs={}; audits={}; types=[]; type_refs={}
        for tn in ['imgsensor_mode_struct','imgsensor_struct']:
            m=re.search(r'typedef struct\s+'+tn+r'\s*\{',masked(htext)); a,b=block(htext,m.start()); b=htext.index(';',b)+1
            body,ref,code=fragment(htext,(a,b),hp['path'],tn,sensor);types.append(code);type_refs[tn]=ref
        types.append(win_type+'\n')
        (SPIKE/'generated'/f'{sensor}-types.inc').write_text(''.join(types))
        modes=parent_extract['sensors'][sensor]['modes']
        pieces.append('static struct { imgsensor_mode_struct '+','.join(modes)+';\n')
        scalar_refs={}
        for field in ['margin','min_shutter','max_frame_length']:
            m=re.search(r'\b(kal_uint\d+)\s+'+field+r'\s*;',masked(htext));assert m
            pieces.append(m[0]+'\n'); scalar_refs[field]=receipt(htext,m.span(),hp['path'])
        pieces.append('} imgsensor_info = {\n')
        for mode,data in modes.items():
            ref=data['provenance'];a=sum(len(x) for x in text.splitlines(keepends=True)[:ref['start_line']-1]); a=text.index('.'+mode,a);span=block(text,a)
            assert receipt(text,span,source)['sha256']==ref['sha256']
            pieces.append(text[slice(*span)]+',\n')
        info_start=text.index('static imgsensor_info_struct imgsensor_info ='); info_span=block(text,info_start)
        for field in scalar_refs:
            m=re.search(r'\.'+field+r'\s*=\s*(0x[\da-fA-F]+|\d+)\s*,',text[slice(*info_span)])
            scalar_refs[field]['initializer']=receipt(text,(info_start+m.start(),info_start+m.end()),source)
            scalar_refs[field]['value']=int(m[1],0);pieces.append(m[0]+'\n')
        pieces.append('};\n')
        for name in names:
            body,ref,code=fragment(text,function(text,name),source,name,sensor)
            clean=masked(body);calls=set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',clean))-{'if','switch','sizeof',name}
            assert calls<=allow,(name,calls-allow)
            assert not re.search(r'^\s*#|\basm\b|->',clean,re.M)
            refs[name]=ref;audits[name]=sorted(calls);pieces.append(code)
        # Feature case fragments retain exact argument conversions. No other feature path is compiled.
        a,b=function(text,'feature_control'); feature=text[a:b]; dispatch_refs={}; feature_pieces=[]
        for key in FEATURES:
            m=re.search(r'case SENSOR_FEATURE_'+key+r'\s*:',feature);assert m
            end=feature.index('break;',m.end())+len('break;')
            body,ref,code=fragment(text,(a+m.start(),a+end),source,'feature-'+key,sensor)
            dispatch_refs[key]=ref; feature_pieces.append(code)
        # Execute only the inner crop switch; pointer decoding and transport remain evidence only.
        crop=feature.index('case SENSOR_FEATURE_GET_CROP_INFO:'); span=block(feature,feature.index('switch',crop))
        crop_body,crop_ref,crop_code=fragment(text,(a+span[0],a+span[1]),source,'crop-switch',sensor)
        getinfo=function(text,'get_info'); g=text[slice(*getinfo)];span=block(g,g.index('switch (scenario_id)'))
        _,grab_ref,grab_code=fragment(text,(getinfo[0]+span[0],getinfo[0]+span[1]),source,'grab-switch',sensor)
        win_start=text.index('static SENSOR_WINSIZE_INFO_STRUCT imgsensor_winsize_info'); win_span=block(text,win_start)
        _,win_ref,win_code=fragment(text,win_span,source,'winsize-declaration',sensor)
        pieces.append(win_code+';\n')
        pieces.append('#line 1 "synthetic-host-feature-wrapper"\nstatic void host_feature(unsigned id, unsigned long long word0, unsigned long long word1) {\n'
                      'unsigned long long payload[2]={word0,word1}; unsigned long long *feature_data=payload;\n'
                      'UINT16 *feature_data_16=(UINT16 *)payload; UINT16 *feature_return_para_16=(UINT16 *)payload;\n'
                      'unsigned length=0; unsigned *feature_para_len=&length; (void)feature_data_16;\n switch(id) {\n'+''.join(feature_pieces)+'}\n'
                      'if(id==SENSOR_FEATURE_GET_PERIOD) { period_query[0]=((UINT16 *)payload)[0]; period_query[1]=((UINT16 *)payload)[1]; } }\n')
        pieces.append('#line 1 "synthetic-host-crop-wrapper"\nstatic void host_crop(unsigned scenario, SENSOR_WINSIZE_INFO_STRUCT *wininfo) {\n'
                      'unsigned *feature_data_32=&scenario;\n'+crop_code+'}\n')
        pieces.append('#line 1 "synthetic-host-grab-wrapper"\nstatic void host_grab(MSDK_SCENARIO_ID_ENUM scenario_id) {\n'
                      'struct { uint16_t SensorGrabStartX,SensorGrabStartY; uint8_t MIPIDataLowPwr2HighSpeedSettleDelayCount; } info;\n'
                      '__typeof__(info) *sensor_info=&info;\n'+grab_code+
                      'grab[0]=info.SensorGrabStartX; grab[1]=info.SensorGrabStartY; }\n')
        (SPIKE/'generated'/f'{sensor}-production.inc').write_text(''.join(pieces))
        result['sensors'][sensor]={'source':cp,'header':hp,'functions':refs,'call_audit':audits,'types':type_refs,
          'scalars':scalar_refs,'feature_fragments':dispatch_refs,'crop_switch':crop_ref,'grab_switch':grab_ref,'winsize_declaration':win_ref,
          'winsize_type':wt,'inherited':parent_extract['sensors'][sensor],
          'new_complete_bodies':['write_shutter','set_shutter'] if sensor=='ov5670' else ['set_shutter'],
          'fragment_scope':'Synthetic wrappers execute exact selected case and switch bytes only; full feature_control/get_info and kernel transport never compiled.'}
    dump(SPIKE/'evidence/extraction.json',result)
    return result

if __name__=='__main__':main()
