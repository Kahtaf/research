#!/usr/bin/env python3
"""Source facts, not Android characteristics or a sensor emulator."""
import json
import re
from fractions import Fraction
from pathlib import Path
from extract import SPIKE, WORKSPACE, SCENARIOS, WRAPPERS, dump, masked, receipt, sha

PAIR_FIELDS = dict(zip(['crop_x_start', 'crop_y_start', 'crop_x_end', 'crop_y_end',
                       'output_width', 'output_height', 'hts', 'vts'], range(0x3800, 0x3810, 2)))
MODE_BY_SCENARIO = dict(zip(SCENARIOS, ['pre', 'cap', 'normal_video', 'hs_video', 'slim_video', 'custom1']))


def rational(value):
    return {'numerator': value.numerator, 'denominator': value.denominator}


def registers(trace):
    regs = {}
    for index, (addr, value, line, fn) in enumerate(trace['writes']):
        regs[addr] = {'value': value, 'valid': True, 'source_line': line, 'function': fn, 'trace_write_index': index}
    return regs


def geometry(trace):
    regs = registers(trace)
    result = {}
    for name, address in PAIR_FIELDS.items():
        valid = address in regs and address + 1 in regs
        result[name] = {'value': regs[address]['value'] * 256 + regs[address+1]['value'] if valid else None,
                        'valid': valid, 'registers': [f'0x{address:04x}', f'0x{address+1:04x}'],
                        'unknown_registers': [f'0x{a:04x}' for a in (address, address+1) if a not in regs]}
    return result


def source_file(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(WORKSPACE)), 'sha256': sha(raw), 'bytes': len(raw)}


def token_ref(path, token):
    text = path.read_text()
    match = re.search(r'^[ \t]*' + re.escape(token) + r'\b', text, re.M)
    assert match, token
    return {'source': str(path.relative_to(WORKSPACE)), 'line': text.count('\n', 0, match.start()) + 1,
            'sha256': sha(path.read_bytes()), 'token': token}


def coverage():
    tag_path = WORKSPACE / '2026-11-06-asus-selected-camera-metadata/inputs/sdk37_camera_metadata_tags.h'
    hal_path = WORKSPACE / '2026-11-06-asus-camera-source-abi-route/fixture/sdk37/hardware/libhardware/include_all/hardware/camera3.h'
    assert sha(tag_path.read_bytes()) == 'bde84090ba7cb609ac4f52163f33c05c4a1d2ad54e46b9ca79fca1117e622613', 'SDK37 metadata tag header changed'
    assert sha(hal_path.read_bytes()) == '52b0e387de7c176af4d9684ab33c5fd1850945c3d22bd8dd316dbd9487af0d04', 'SDK37 camera3 header changed'
    categories = [
        ('geometry', ['ANDROID_SENSOR_INFO_PIXEL_ARRAY_SIZE', 'ANDROID_SENSOR_INFO_ACTIVE_ARRAY_SIZE', 'ANDROID_SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE', 'ANDROID_SCALER_CROP_REGION'],
         'Partial source inputs: programmed output bytes, partial crop registers, OEM grab windows and winsize stages. Coordinate transforms, optical/black borders and Android array origins remain unresolved. No Android size/rectangle emitted.'),
        ('timing', ['ANDROID_SENSOR_FRAME_DURATION', 'ANDROID_SENSOR_INFO_MAX_FRAME_DURATION', 'ANDROID_SENSOR_INFO_EXPOSURE_TIME_RANGE', 'ANDROID_CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES', 'ANDROID_CONTROL_AE_TARGET_FPS_RANGE'],
         'Partial source inputs: declared pclk, HTS/VTS, tenths-rate declarations and exact timing-setter writes. Not physical clock qualification, exposure/3A behavior or end-to-end FPS support. No range or duration advertised.'),
        ('streams_and_isp', ['ANDROID_SCALER_AVAILABLE_STREAM_CONFIGURATIONS', 'ANDROID_SCALER_AVAILABLE_MIN_FRAME_DURATIONS', 'ANDROID_SCALER_AVAILABLE_STALL_DURATIONS', 'ANDROID_CONTROL_AVAILABLE_HIGH_SPEED_VIDEO_CONFIGURATIONS', 'ANDROID_REQUEST_MAX_NUM_OUTPUT_STREAMS'],
         'Unresolved ISP formats, buffer layouts, stream sizes/combinations, throughput and stalls. Sensor output registers do not establish Android streams or constrained-high-speed capability.'),
        ('3a_and_results', ['ANDROID_CONTROL_AE_AVAILABLE_MODES', 'ANDROID_CONTROL_AF_AVAILABLE_MODES', 'ANDROID_CONTROL_AWB_AVAILABLE_MODES', 'ANDROID_SENSOR_SENSITIVITY', 'ANDROID_SENSOR_EXPOSURE_TIME', 'ANDROID_SENSOR_TIMESTAMP', 'ANDROID_REQUEST_PIPELINE_MAX_DEPTH'],
         'Unresolved supported controls, default values, tuning, requests/results, ISO/gain mapping, timestamp provenance, synchronization and pipeline latency. No 3A or result implementation executed.'),
        ('lens_calibration', ['ANDROID_LENS_INFO_AVAILABLE_FOCAL_LENGTHS', 'ANDROID_LENS_INFO_AVAILABLE_APERTURES', 'ANDROID_LENS_INFO_MINIMUM_FOCUS_DISTANCE', 'ANDROID_LENS_INTRINSIC_CALIBRATION', 'ANDROID_SENSOR_CALIBRATION_TRANSFORM1', 'ANDROID_SENSOR_INFO_PHYSICAL_SIZE'],
         'Unresolved. No private calibration, OTP, lens data, DNG/NVRAM constructor or another sensor constructor used.'),
        ('orientation_and_identity', ['ANDROID_SENSOR_ORIENTATION', 'ANDROID_LENS_FACING', 'ANDROID_LOGICAL_MULTI_CAMERA_PHYSICAL_IDS'],
         'Unresolved logical camera IDs, facing and orientation. Parent cached main/sub driver selection only; no logical/multi-camera capability implied.'),
        ('jpeg', ['ANDROID_JPEG_MAX_SIZE', 'ANDROID_JPEG_AVAILABLE_THUMBNAIL_SIZES'],
         'Unresolved JPEG encoder behavior, size bounds, thumbnails and stall times.'),
        ('contract_and_keys', ['ANDROID_INFO_SUPPORTED_HARDWARE_LEVEL', 'ANDROID_REQUEST_AVAILABLE_CAPABILITIES', 'ANDROID_REQUEST_AVAILABLE_REQUEST_KEYS', 'ANDROID_REQUEST_AVAILABLE_RESULT_KEYS', 'ANDROID_REQUEST_AVAILABLE_CHARACTERISTICS_KEYS', 'ANDROID_REQUEST_AVAILABLE_SESSION_KEYS'],
         'Unresolved contract and conditional requirements. A key list or capability must follow implemented pipeline behavior, not sensor declarations. No version, capability or hardware-level values generated.'),
    ]
    result = {'scope': 'SDK37 category coverage candidates; exact requirements depend on eventual hardware level/capabilities. Header token presence is schema evidence, not a complete Android compliance specification.',
              'headers': [source_file(tag_path), source_file(hal_path)], 'characteristics_and_request_categories': [], 'templates': []}
    for category, tags, text in categories:
        result['characteristics_and_request_categories'].append({'category': category, 'coverage': text,
             'sdk37_tokens': [token_ref(tag_path, t) for t in tags], 'metadata_values_emitted': False})
    for template, text in [
        ('PREVIEW', 'Source pre mode is a geometry/timing candidate only. AE/AWB/AF, pipeline outputs and valid defaults remain unresolved.'),
        ('STILL_CAPTURE', 'Source cap/cap1 branching is a candidate only. JPEG, lens/3A controls and actual exposure/results remain unresolved.'),
        ('VIDEO_RECORD', 'Source normal_video is a candidate only. Supported stream combinations, sustained FPS and 3A remain unresolved.'),
        ('VIDEO_SNAPSHOT', 'No concurrent still/video stream or timing contract established.'),
        ('ZERO_SHUTTER_LAG', 'No reprocessing, buffered frame selection or ZSL contract established.'),
        ('MANUAL', 'No qualified exposure/sensitivity/focus range or manual request/result contract established.')]:
        result['templates'].append({'schema': token_ref(hal_path, 'CAMERA3_TEMPLATE_' + template), 'coverage': text,
                                    'supported': None, 'request_template_emitted': False})
    result['default_request_requirement'] = {'source': str(hal_path.relative_to(WORKSPACE)), 'start_line': 3213, 'end_line': 3242,
         'note': 'Use-case settings depend on supported capabilities; null settings for supported templates are a fatal contract failure. No template is implemented by this unit.'}
    dump(SPIKE / 'evidence/metadata-input-coverage.json', result)


def main():
    extraction = json.loads((SPIKE / 'evidence/extraction.json').read_text())
    ledger = {'schema': 1, 'status': 'source-evidence-only', 'hardware_qualified': False,
              'provenance_rules': {'source': 'Inherited per sensor source path and full-file hash; each declaration has exact line. Function receipts include exact byte SHA256 and range in evidence/extraction.json.',
                  'register': 'Last-write-wins trace with source line, unchanged function, trace index; only written bytes are valid. Unknown is null, never zero.',
                  'derived': 'Big-endian concatenation of complete register pairs; rational clock/(HTS*VTS) uses declared pclk, not measured/PLL-derived clock. No active-array or delivered-frame interpretation.',
                  'scenario_labels': 'Symbolic host fixture labels; not a witness of numeric kernel enum/status ABI.',
                  'fixture_state': 'Zeroed host software state and caller-selected current_fps; these are test inputs, not sensor power-on defaults.'},
              'sensors': {}}
    prior_path = WORKSPACE / '2026-11-06-asus-selected-camera-metadata/evidence/mapping.json'
    prior = json.loads(prior_path.read_text())
    for sensor, data in extraction['sensors'].items():
        traces = json.loads((SPIKE / 'evidence' / f'{sensor}-traces.json').read_text())
        index = {t['case']: t for t in traces}
        source = WORKSPACE / data['source']
        text = source.read_text()
        identity = next(p for p in prior['paths'] if p['sensor'].lower() == sensor)
        facts = {'source': data['source'], 'source_sha256': data['source_sha256'],
                 'selection': {k: identity[k] for k in ['cached_selected_driver', 'role_from_oem_enum', 'logical_camera_id', 'facing_qualified']},
                 'selection_provenance': {'source': str(prior_path.relative_to(WORKSPACE)), 'sha256': sha(prior_path.read_bytes()),
                                          'json_pointer': '/paths/' + str(prior['paths'].index(identity))},
                 'declared_modes': data['modes'], 'declared_winsize': data['winsize'],
                 'crop_info_dispatch': data['crop_dispatch'], 'scenario_programs': [], 'findings': [],
                 'unknown_dependencies': ['No sensor_init body, register-default subset, probe, OTP or calibration was executed.',
                       'Unwritten crop bytes remain unknown even across these tested mode transitions.',
                       'PLL state and other unrecorded initialization dependencies are not resolved; source pclk is not independently proven.',
                       'Register mask/units interpretation beyond the OEM timing setters and conventional 16-bit geometry pairs is not a datasheet validation.']}
        for scenario, mode in MODE_BY_SCENARIO.items():
            if mode not in data['modes']:
                continue
            fps = 150 if scenario == 'CAMERA_CAPTURE_JPEG' and sensor == 'ov5670' else 300
            representative = [(f'control/{scenario}/{fps}', 'cap1' if scenario == 'CAMERA_CAPTURE_JPEG' and sensor == 'ov5670' else mode)]
            if scenario == 'CAMERA_CAPTURE_JPEG':
                representative = [('capture/300', 'cap'), (f'capture/{150 if sensor == "ov5670" else 240}', 'cap1')]
            for case, declared_mode in representative:
                trace = index[case]
                geo = geometry(trace)
                regs = registers(trace)
                fields = data['modes'][declared_mode]['fields']
                mapping = next((m for m in data['crop_dispatch']['mapping'] if 'MSDK_SCENARIO_ID_' + scenario in m['labels']), None)
                if mapping is None:
                    mapping = next(m for m in data['crop_dispatch']['mapping'] if 'default' in m['labels'])
                win = data['winsize'][mapping['winsize_index']]['fields']
                pclk, hts, vts = fields['pclk']['value'], geo['hts']['value'], geo['vts']['value']
                output = [geo['output_width']['value'], geo['output_height']['value']]
                grab = [fields['grabwindow_width']['value'], fields['grabwindow_height']['value']]
                row = {'scenario': 'MSDK_SCENARIO_ID_' + scenario, 'declared_mode': declared_mode, 'case': case,
                       'trace': f'evidence/{sensor}-traces.json#/{traces.index(trace)}',
                       'geometry': geo, 'register_bytes': {f'0x{a:04x}': regs.get(a, {'value': None, 'valid': False}) for a in range(0x3800, 0x3810)},
                       'source_clock_over_programmed_timing_hz': rational(Fraction(pclk, hts*vts)),
                       'source_timing_period_ns': rational(Fraction(hts*vts*10**9, pclk)),
                       'declared_max_framerate_tenths': fields['max_framerate'],
                       'declared_rate_hz': rational(Fraction(fields['max_framerate']['value'], 10)),
                       'fps_difference_hz': rational(Fraction(pclk, hts*vts) - Fraction(fields['max_framerate']['value'], 10)),
                       'comparison': {'programmed_output': output, 'declared_grab_window': grab,
                            'crop_dispatch_winsize_index': mapping['winsize_index'], 'crop_dispatch_line': mapping['line'],
                            'winsize_stage1': [win['w1_size'], win['h1_size']], 'winsize_target': [win['w2_tg_size'], win['h2_tg_size']],
                            'output_equals_grab': output == grab, 'output_equals_winsize_stage1': output == [win['w1_size'], win['h1_size']],
                            'grab_equals_winsize_target': grab == [win['w2_tg_size'], win['h2_tg_size']],
                            'timing_equals_declared': [hts, vts] == [fields['linelength']['value'], fields['framelength']['value']],
                            'crop_rectangle_resolved': all(geo[n]['valid'] for n in ['crop_x_start','crop_y_start','crop_x_end','crop_y_end']),
                            'android_active_array_resolved': False}}
                facts['scenario_programs'].append(row)
        for trace in traces:
            if trace['case'].startswith(('capture-then-', 'scenario-rate/', 'default-rate/', 'flicker-', 'direct-rate/', 'video-scenario-rate-zero')):
                facts.setdefault('setter_and_lookup_witnesses', []).append({'case': trace['case'],
                    'state': trace['state'], 'state_provenance': 'Exact wrappers/setter receipts in extraction.json; trace fixture state is not a reset default.',
                    'default_rate_query': trace['default_rate_query'] if trace['case'].startswith('default-rate/') else None,
                    'new_register_writes': len(trace['writes']) - trace['stage_boundary'],
                    'hts': geometry(trace)['hts']['value'], 'vts': geometry(trace)['vts']['value'],
                    'trace': f'evidence/{sensor}-traces.json#/{traces.index(trace)}'})
        if sensor == 'ov5670':
            facts['findings'] += [
                {'kind': 'incomplete_mapping', 'message': 'custom1 control selects custom1 body, but crop-info uses default row 0; declared row 5 is not dispatched. Rows 0 and 5 currently contain identical numbers.', 'provenance': data['crop_dispatch']['provenance']},
                {'kind': 'incomplete_mapping', 'message': 'custom1 default-rate lookup leaves sentinel untouched; scenario-rate setter falls through to preview arithmetic.', 'provenance': [data['functions'][f] for f in ['control','get_default_framerate_by_scenario','set_max_framerate_by_scenario']]},
                {'kind': 'distinct_geometry', 'message': 'Output 1296x972 / 2592x1944 / 644x480 differs from grab-window 1280x960 / 2560x1920 / 640x480. No Android coordinate mapping established.', 'provenance': 'scenario_programs and declared_modes above'}]
        else:
            facts['findings'].append({'kind': 'rate_state_vs_register', 'message': 'cap1 max=240 tenths; capture still writes base VTS=1294. Scenario-rate(240) computes state VTS=1617 with zero writes. Legacy set_video_mode(240) invokes set_dummy and writes VTS=1617. No claim that this legacy path is used by HAL3.', 'provenance': [data['functions'][f] for f in ['capture','capture_setting','preview_setting','set_max_framerate_by_scenario','set_video_mode','set_max_framerate','set_dummy']]})
        facts['findings'].append({'kind': 'rate_qualification', 'message': 'Exact source-clock ratios and nominal max_framerate/10 are distinct. Small rational differences can reflect nominal rounding; differing PLL writes and unknown defaults prevent interpreting ratios as measured delivered FPS.', 'provenance': 'scenario_programs rational fields and exact mode declarations'})
        ledger['sensors'][sensor] = facts
    # Compact machine ledger; extraction.json retains indented source receipts.
    (SPIKE / 'evidence/sensor-facts.json').write_text(json.dumps(ledger, separators=(',', ':')) + '\n')
    coverage()
    print('Sensor-facts ledger and SDK37 coverage written; no HAL characteristics/templates emitted.')


if __name__ == '__main__':
    main()
