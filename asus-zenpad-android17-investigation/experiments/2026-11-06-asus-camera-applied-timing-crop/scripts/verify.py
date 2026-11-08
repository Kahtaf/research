"""Independent integer model plus behavioral and provenance assertions."""
import copy
import json
from fractions import Fraction
from extract import SPIKE, PARENT, ROOT, sha, dump

WIN_FIELDS='full_w full_h x0_offset y0_offset w0_size h0_size scale_w scale_h x1_offset y1_offset w1_size h1_size x2_tg_offset y2_tg_offset w2_tg_size h2_tg_size'.split()


def model(spec, meta, sensor):
    modes={k:{f:v['value'] for f,v in d['fields'].items()} for k,d in meta['inherited']['modes'].items()}
    scalars={k:v['value'] for k,v in meta['scalars'].items()}; margin=scalars['margin']; maximum=scalars['max_frame_length']
    state=dict(spec['inherited_seed']['state'],shutter=0,autoflicker_en=int(spec.get('flicker',False)))
    state.update(spec.get('synthetic_state',{}));writes=[];stages=[];period=[0,0]
    def snap(stage):stages.append({'stage':stage,'state':state.copy(),'period':period.copy(),'writes':writes.copy()})
    def pair(address,value):writes.extend([[address,(value>>8)&255],[address+1,value&255]])
    def rate_apply(rate,update_min):
        desired=(((state['pclk']//rate)*10)&0xffffffff)//state['line_length']
        state['frame_length']=min(max(desired,state['min_frame_length']),maximum)
        state['dummy_line']=((state['frame_length']-state['min_frame_length'])&0xffffffff)&65535
        if update_min:state['min_frame_length']=state['frame_length']
        pair(0x380e,state['frame_length']);pair(0x380c,state['line_length'])
    snap('seed')
    if 'rate' in spec:
        mode=modes['cap1' if state['current_fps']==modes['cap1']['max_framerate'] else 'cap']
        rate=spec['rate']&0xffffffff
        assert rate>0
        desired=(((mode['pclk']//rate)*10)&0xffffffff)//mode['linelength']
        state['dummy_line']=max(desired-mode['framelength'],0)&65535
        state['frame_length']=mode['framelength']+state['dummy_line'];state['min_frame_length']=state['frame_length']
        snap('scenario-rate')
    if 'set_fps' in spec:state['current_fps']=spec['set_fps']&65535;snap('set-framerate')
    if 'video_rate' in spec:
        rate=spec['video_rate']&65535
        if rate:
            state['current_fps']={300:296,150:146}.get(rate,rate) if state['autoflicker_en'] else rate
            rate_apply(state['current_fps'],True)
        snap('video-rate')
    period=[state['line_length']&65535,state['frame_length']&65535];snap('period-before')
    requested=spec['shutter']&65535;state['shutter']=requested
    shutter=max(requested,1) if sensor=='ov2680' else requested
    threshold=(state['min_frame_length']-margin)&0xffffffff
    frame=shutter+margin if shutter>threshold else state['min_frame_length']
    frame=min(frame,maximum)
    shutter=max(shutter,scalars['min_shutter']);shutter=min(shutter,maximum-margin)
    if sensor=='ov5670':frame &= ~1;shutter &= ~1
    state['frame_length']=frame
    fps=(((state['pclk']//state['line_length'])*10)&0xffffffff)//frame
    fps &= 65535
    if state['autoflicker_en'] and (297<=fps<=305 or 147<=fps<=150):
        rate_apply(296 if 297<=fps<=305 else 146,False)
    else:pair(0x380e,state['frame_length'])
    writes.extend([[0x3502,(shutter<<4)&(0xf0 if sensor=='ov5670' else 255)], [0x3501,(shutter>>4)&255],[0x3500,(shutter>>12)&15]])
    snap('exposure');period=[state['line_length']&65535,state['frame_length']&65535];snap('period-after')
    return stages


def main(extraction):
    checks=[];ledger={'schema':1,'status':'source-evidence-only','hardware_qualified':False,'sensors':{},
      'register_policy':'Only inherited/recorded bytes are known; null for absent bytes. No reset/default/high-byte assumptions. Raw VTS pair is not a measured frame cadence or decoded reserved-bit contract.',
      'stage_policy':'Sensor register rectangle, winsize source/crop/scale/TG fields, OEM grab start/size, ISP coordinates and Android active-array/streams remain separate.',
      'metadata_emitted':False,'templates_supported':False}
    assertions=0
    for sensor,meta in extraction['sensors'].items():
        traces=json.loads((SPIKE/'evidence'/f'{sensor}-traces.json').read_text())
        specs=json.loads((SPIKE/'evidence'/f'{sensor}-cases.json').read_text())
        groups={s['label']:[t for t in traces if t.get('case')==s['label']] for s in specs}
        facts=[]
        for spec in specs:
            actual=groups[spec['label']];expected=model(spec,meta,sensor)
            assert len(actual)==len(expected)
            for a,e in zip(actual,expected):
                assert a['stage']==e['stage'] and a['state']==e['state'] and a['period']==e['period'],(sensor,spec['label'],a,e)
                assert [w[:2] for w in a['writes']]==e['writes'],(sensor,spec['label'],a,e)
                for w in a['writes']:
                    ref=meta['functions'][w[3]]
                    assert ref['start_line']<=w[2]<=ref['end_line']
                    source_line=(ROOT/ref['source']).read_text().splitlines()[w[2]-1]
                    assert 'write_cmos_sensor' in source_line
                assertions+=1
            prior={};provenance={}
            for i,w in enumerate(spec['inherited_seed']['writes']):
                prior[w[0]]=w[1];provenance[w[0]]={'kind':'inherited-accepted-mode-write','case':spec['seed'],'index':i,'line':w[2],'function':w[3],'source':meta['source']['path'],'source_sha256':meta['source']['sha256']}
            stages=[]
            for t in actual:
                registers=prior.copy();refs=copy.deepcopy(provenance)
                for i,w in enumerate(t['writes']):
                    registers[w[0]]=w[1];refs[w[0]]={'kind':'new-host-recorded-write','index':i,'line':w[2],'function':w[3],**meta['functions'][w[3]]}
                def pair(address):
                    return (registers[address]<<8)|registers[address+1] if address in registers and address+1 in registers else None
                vts=pair(0x380e);hts=pair(0x380c)
                ratio=Fraction(t['state']['pclk'],hts*vts) if hts and vts else None
                encoded_shutter=((registers[0x3500]&15)<<12)|(registers[0x3501]<<4)|(registers[0x3502]>>4) if all(a in registers for a in [0x3500,0x3501,0x3502]) else None
                stages.append({'stage':t['stage'],'state':t['state'],'get_period_payload':t['period'],
                  'new_write_count':len(t['writes']),'encoded_coarse_shutter_lines':encoded_shutter,'vts_minus_encoded_shutter':vts-encoded_shutter if vts is not None and encoded_shutter is not None else None,'applied_hts_pair':hts,'applied_vts_pair':vts,
                  'declared_clock_over_register_timing_hz':{'numerator':ratio.numerator,'denominator':ratio.denominator} if ratio else None,
                  'register_bytes':{f'0x{a:04x}':{'value':registers.get(a),'provenance':refs.get(a)} for a in [*range(0x3800,0x3810),0x3500,0x3501,0x3502]}})
            facts.append({'case':spec['label'],'seed':spec['seed'],'fixture_overrides':spec.get('synthetic_state'),
                          'feature_words':{k:spec[k] for k in ['rate','shutter','set_fps','video_rate'] if k in spec},'stages':stages})
        # Semantic checks independent of broad arithmetic model.
        simple=next(f for f in facts if f['case']=='rate-240-shutter-100')
        b=next(x for x in simple['stages'] if x['stage']=='scenario-rate');e=next(x for x in simple['stages'] if x['stage']=='exposure')
        assert b['new_write_count']==0 and b['state']['frame_length']!=b['applied_vts_pair']
        assert e['new_write_count']==5 and e['state']['frame_length']==e['applied_vts_pair']
        assert (b['state']['frame_length'],e['applied_vts_pair'])==((2556,2556) if sensor=='ov5670' else (1617,1617))
        for stage in simple['stages']:
            assert stage['register_bytes']['0x3800']['value'] is None
            assert stage['register_bytes']['0x3802']['value'] is None
        zero=next(f for f in facts if f['case']=='rate-300-shutter-0')['stages'][-1]
        assert zero['state']['shutter']==0 and zero['encoded_coarse_shutter_lines']==(4 if sensor=='ov5670' else 1)
        maximum=next(f for f in facts if f['case']=='rate-300-shutter-65535')['stages'][-1]
        assert (maximum['applied_vts_pair'],maximum['encoded_coarse_shutter_lines'])==((32766,32762) if sensor=='ov5670' else (32767,32763))
        narrowed=next(f for f in facts if f['case']=='rate-300-shutter-65536')['stages'][-1]
        assert narrowed['state']['shutter']==0 and narrowed['encoded_coarse_shutter_lines']==zero['encoded_coarse_shutter_lines']
        clamped=next(f for f in facts if f['case']=='scenario-then-legacy-clamp')
        before=next(t for t in clamped['stages'] if t['stage']=='scenario-rate')
        after=next(t for t in clamped['stages'] if t['stage']=='video-rate')
        assert after['new_write_count']==4 and after['state']['frame_length']<=32767
        if sensor=='ov2680':
            assert before['state']['min_frame_length']==60555
            assert after['state']['dummy_line']==37748 # uint32 subtraction then uint16 conversion
        for boundary in [146,147,150,151,296,297,305,306]:
            case=next(f for f in facts if f['case']==f'flicker-boundary-{boundary}')
            exposure=next(t for t in case['stages'] if t['stage']=='exposure')
            assert exposure['new_write_count']==(7 if boundary in [147,150,297,305] else 5)
        # No mode execution: inherited trace supplies initial known/unknown register bytes only.
        crop_results=[t for t in traces if 'crop' in t];assert len(crop_results)==7
        crop_facts=[];decl=meta['inherited']['winsize'];mapping=meta['inherited']['crop_dispatch']['mapping']
        for item in crop_results:
            scenario='MSDK_SCENARIO_ID_'+item['crop']
            selected=next((m for m in mapping if scenario in m['labels']),next(m for m in mapping if 'default' in m['labels']))
            row=decl[selected['winsize_index']]
            assert item['winsize']==[row['fields'][f] for f in WIN_FIELDS]
            mode={'CAMERA_PREVIEW':'pre','CAMERA_CAPTURE_JPEG':'cap','VIDEO_PREVIEW':'normal_video','HIGH_SPEED_VIDEO':'hs_video','SLIM_VIDEO':'slim_video','CUSTOM1':'custom1' if sensor=='ov5670' else 'pre','INVALID':'pre'}[item['crop']]
            fields=meta['inherited']['modes'][mode]['fields']
            assert item['grab']==[fields['startx']['value'],fields['starty']['value']]
            crop_facts.append({'scenario':item['crop'],'winsize_index':selected['winsize_index'],'winsize':dict(zip(WIN_FIELDS,item['winsize'])),
              'winsize_provenance':row['provenance'],'crop_dispatch':meta['crop_switch'],'grab_start':item['grab'],
              'grab_dimensions':[fields['grabwindow_width']['value'],fields['grabwindow_height']['value']],
              'grab_provenance':meta['grab_switch'],'grab_mode_declaration':meta['inherited']['modes'][mode]['provenance'],
              'isp_transform':None,'android_active_array_transform':None})
            assertions+=1
        ledger['sensors'][sensor]={'source':meta['source'],'new_complete_bodies':meta['new_complete_bodies'],'functions':meta['functions'],
          'scalars':meta['scalars'],'timing_cases':facts,'crop_stages':crop_facts,
          'observed_nominal_240_case':{'state_only_frame_length':b['state']['frame_length'],'prior_applied_vts':b['applied_vts_pair'],'exposure_applied_vts':e['applied_vts_pair']}}
        checks.append({'sensor':sensor,'timing_sequences':len(specs),'stage_observations':sum(len(v) for v in groups.values()),'crop_cases':len(crop_results),
          'checks':['independent width-preserving arithmetic and ordered writes','original write lines/functions','state-only vs exposure apply','GET_PERIOD software state vs applied registers',
                    'feature word narrowing','shutter zero/minimum/odd/max/margin','flicker inclusivity and dummy HTS writes','uint16 dummy_line truncation','crop dispatch/custom1/default','grab switch mapping','unknown crop high bytes retained']})
    dump(SPIKE/'evidence/applied-timing-crop.json',ledger)
    dump(SPIKE/'evidence/verification.json',{'passed':True,'stage_and_crop_comparisons':assertions,'checks':checks,
      'new_complete_production_bodies':3,'reused_complete_timing_bodies':8,'full_drivers_or_transport_compiled':False,'mode_programs_executed':False,
      'excluded_invalid_inputs':['zero framerate at unguarded scenario/direct division','invalid/undersized external pointers or transport payload','actual hardware exposure']})

if __name__=='__main__':
    from extract import main as extract
    main(extract())
