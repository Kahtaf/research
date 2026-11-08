#!/usr/bin/env python3
"""Pinned public-source extraction. Never imports or builds the OEM driver."""
import hashlib
import json
import re
from pathlib import Path

SPIKE = Path(__file__).resolve().parents[1]
WORKSPACE = SPIKE.parent
PIN_PATH = WORKSPACE / '2026-11-06-asus-camera-metadata-source-inputs/evidence/asus-sensor-source-pins.json'
EXPECTED = {
    'ov5670mipi_Sensor.c': 'aad8723995f1e02d3202bd9b0d085eaeca98cd93829379c8550d69fd29cfd7fc',
    'ov5670mipi_Sensor.h': 'b5ee4568eae2903d72cb99d13ddbfa57f9c100e7cebb0338f72219bad6cdba4a',
    'ov2680mipi_Sensor.c': 'e0d768a30788e0027df9160c95024f9e4d418438915efb68f7c3263d896eabff',
    'ov2680mipi_Sensor.h': 'a40bfc5dfb8bf387bf9ffb91096a36cf80d45cbd2876df86074df93eeca88398',
}
SUPPORT_PINS = {
    'COPYING': 'af8067302947c01fd9eee72befa54c7e3ef8a48fecde7fd71277f2290b2bf0f7',
    'drivers/misc/mediatek/imgsensor/inc/kd_imgsensor_define.h': '582b64b65c2df1b8775e61347eb5ae5f125f052d2c7b337e1fc96ca280a7eaf8',
}
MODE_FIELDS = 'pclk linelength framelength startx starty grabwindow_width grabwindow_height mipi_data_lp2hs_settle_dc max_framerate'.split()
WIN_FIELDS = 'full_w full_h x0_offset y0_offset w0_size h0_size scale_w scale_h x1_offset y1_offset w1_size h1_size x2_tg_offset y2_tg_offset w2_tg_size h2_tg_size'.split()
SCENARIOS = ['CAMERA_PREVIEW', 'CAMERA_CAPTURE_JPEG', 'VIDEO_PREVIEW', 'HIGH_SPEED_VIDEO', 'SLIM_VIDEO', 'CUSTOM1']
WRAPPERS = ['preview', 'capture', 'normal_video', 'hs_video', 'slim_video']
BASE_FUNCTIONS = ['set_dummy', 'set_max_framerate', 'preview_setting', 'capture_setting', 'normal_video_setting', 'hs_video_setting', 'slim_video_setting']
TAIL_FUNCTIONS = ['control', 'set_video_mode', 'set_max_framerate_by_scenario', 'get_default_framerate_by_scenario']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def masked(text):
    """Preserve offsets/newlines while masking comments and literals."""
    pattern = r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.S)


def block(text, start):
    clean = masked(text)
    brace = clean.index('{', start)
    depth = 0
    for pos in range(brace, len(clean)):
        if clean[pos] == '{':
            depth += 1
        elif clean[pos] == '}':
            depth -= 1
            if not depth:
                return start, pos + 1
    raise ValueError('Unterminated source block')


def function(text, name):
    matches = list(re.finditer(r'^static\s+\w+\s+' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', masked(text), re.M))
    assert len(matches) == 1, (name, len(matches))
    return block(text, matches[0].start())


def receipt(text, span, source):
    start, end = span
    data = text[start:end].encode()
    return {'source': source, 'start_line': text.count('\n', 0, start) + 1,
            'end_line': text.count('\n', 0, end) + 1, 'sha256': sha(data), 'bytes': len(data)}


def validate_pins(root=WORKSPACE, pins=None):
    pins = pins if pins is not None else json.loads(PIN_PATH.read_text())['files']
    assert len(pins) == 4
    for pin in pins:
        path = root / pin['path']
        assert pin['sha256'] == EXPECTED[path.name], f'parent pin changed: {path.name}'
        raw = path.read_bytes()
        assert sha(raw) == pin['sha256'] and len(raw) == pin['bytes'], f'source pin mismatch: {path}'
    return pins


def extract_sensor(sensor, pin):
    source = pin['path']
    raw = (WORKSPACE / source).read_bytes()
    text = raw.decode()
    assert '\r' not in text, 'Byte-preserving LF extraction expected'
    # Retain untouched public originals, including notices; never compile these copies.
    (SPIKE / 'inputs' / Path(source).name).write_bytes(raw)
    header_source = str(Path(source).with_suffix('.h'))
    header_text = (WORKSPACE / header_source).read_text()
    type_receipts = {}
    type_pieces = ['/* Exact OEM mode/state types. Symbolic scalar/enum fixtures precede these. */\n']
    for type_name in ['imgsensor_mode_struct', 'imgsensor_struct']:
        match = re.search(r'typedef struct\s+' + type_name + r'\s*\{', masked(header_text))
        assert match
        span = block(header_text, match.start())
        end = header_text.index(';', span[1]) + 1
        span = (span[0], end)
        ref = receipt(header_text, span, header_source)
        type_receipts[type_name] = ref
        type_pieces.append(f'#line {ref["start_line"]} "{header_source}"\n' + header_text[span[0]:span[1]] + '\n')
    (SPIKE / 'generated' / f'{sensor}-types.inc').write_text(''.join(type_pieces))
    info_start = text.index('static imgsensor_info_struct imgsensor_info =')
    info_span = block(text, info_start)
    info = text[info_span[0]:info_span[1]]
    mode_names = ['pre', 'cap', 'cap1', 'normal_video', 'hs_video', 'slim_video']
    if sensor == 'ov5670':
        mode_names.append('custom1')
    modes = {}
    mode_blocks = []
    for mode in mode_names:
        match = re.search(r'\.' + mode + r'\s*=\s*\{', masked(info))
        assert match, mode
        local = block(info, match.start())
        span = (info_start + local[0], info_start + local[1])
        mode_text = text[span[0]:span[1]]
        fields = {}
        for key in MODE_FIELDS:
            m = re.search(r'\.' + key + r'\s*=\s*(0x[\da-fA-F]+|\d+)\s*,', masked(mode_text))
            assert m, (mode, key)
            value = int(m[1], 0)
            fields[key] = {'value': value, 'line': text.count('\n', 0, span[0] + m.start()) + 1}
        modes[mode] = {'fields': fields, 'provenance': receipt(text, span, source)}
        mode_blocks.append((span, mode_text))
    max_match = re.search(r'\.max_frame_length\s*=\s*(0x[0-9a-f]+)', info)
    maximum = {'value': int(max_match[1], 16), 'line': text.count('\n', 0, info_start + max_match.start()) + 1}
    win_start = text.index('static SENSOR_WINSIZE_INFO_STRUCT imgsensor_winsize_info')
    win_span = block(text, win_start)
    win_text = text[win_span[0]:win_span[1]]
    wins = []
    for row in re.finditer(r'\{\s*(\d[^{}]*)\}', masked(win_text)):
        numbers = [int(v.strip(), 10) for v in row[1].split(',')]
        assert len(numbers) == len(WIN_FIELDS)
        span = (win_start + row.start(), win_start + row.end())
        wins.append({'index': len(wins), 'fields': dict(zip(WIN_FIELDS, numbers)), 'provenance': receipt(text, span, source)})
    assert len(wins) == (6 if sensor == 'ov5670' else 5)
    names = BASE_FUNCTIONS + (['custom1_setting'] if sensor == 'ov5670' else []) + WRAPPERS + (['custom1'] if sensor == 'ov5670' else []) + TAIL_FUNCTIONS
    allowed = set(names) | {'LOG_INF', 'LOG_DBG', 'mdelay', 'spin_lock', 'spin_unlock', 'write_cmos_sensor'}
    bodies, dependencies = {}, {}
    pieces = [text[:text.index('#include')], '\n/* Host fixtures supply types; all function bodies below are byte-exact. */\n']
    pieces.append('static struct { imgsensor_mode_struct ' + ', '.join(mode_names) + '; kal_uint32 max_frame_length; } imgsensor_info = {\n')
    for span, body in mode_blocks:
        pieces.append(f'#line {receipt(text, span, source)["start_line"]} "{source}"\n' + body + ',\n')
    pieces.append(f'.max_frame_length = {maximum["value"]}\n}};\n')
    for name in names:
        span = function(text, name)
        body = text[span[0]:span[1]]
        clean = masked(body)
        calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', clean)) - {'if', 'switch', 'sizeof', name}
        assert calls <= allowed, f'Unreviewed call from {name}: {calls - allowed}'
        assert not re.search(r'^\s*#', clean, re.M), f'Unreviewed preprocessor in {name}'
        # No pointer dereference, arbitrary I/O, assembly or non-whitelisted calls in selected bodies.
        assert not re.search(r'\basm\b|->', clean)
        dependencies[name] = {'calls': sorted(calls), 'info_fields': sorted(set(re.findall(r'imgsensor_info\.([\w.]+)', clean))),
                              'state_fields': sorted(set(re.findall(r'imgsensor\.([\w]+)', clean)))}
        bodies[name] = receipt(text, span, source)
        (SPIKE / 'generated' / f'{sensor}-{name}.inc').write_bytes(body.encode())
        pieces.append(f'#line {bodies[name]["start_line"]} "{source}"\n' + body + '\n')
    (SPIKE / 'generated' / f'{sensor}-production.inc').write_text(''.join(pieces))
    # Feature dispatch is evidence only: do not compile feature_control (contains unsafe paths).
    feature_span = function(text, 'feature_control')
    feature = text[feature_span[0]:feature_span[1]]
    crop_start = feature.index('case SENSOR_FEATURE_GET_CROP_INFO:')
    # Capture the complete nested switch with balanced braces, plus the case label.
    switch_span = block(feature, feature.index('switch', crop_start))
    crop_span = (feature_span[0] + crop_start, feature_span[0] + switch_span[1])
    crop_text = text[crop_span[0]:crop_span[1]]
    (SPIKE / 'generated' / f'{sensor}-crop-dispatch.txt').write_text(crop_text)
    mapping = []
    labels = []
    for match in re.finditer(r'case\s+(MSDK_SCENARIO_ID_\w+)\s*:|\b(default)\s*:|imgsensor_winsize_info\[(\d+)\]', masked(crop_text)):
        if match[1] or match[2]:
            labels.append(match[1] or 'default')
        else:
            mapping.append({'labels': labels, 'winsize_index': int(match[3]), 'line': text.count('\n', 0, crop_span[0] + match.start()) + 1})
            labels = []
    return {'source': source, 'source_sha256': pin['sha256'], 'modes': modes, 'winsize': wins, 'types': type_receipts,
            'max_frame_length': maximum, 'functions': bodies, 'dependency_audit': dependencies,
            'crop_dispatch': {'provenance': receipt(text, crop_span, source), 'mapping': mapping},
            'excluded': ['sensor_init', 'open', 'close', 'get_imgsensor_id', 'read_cmos_sensor', 'feature_control', 'OTP/debugfs/proc/calibration functions', 'set_shutter and gain paths'],
            'defaults_executed': False}


def main():
    pins = validate_pins()
    result = {'schema': 1, 'pins': pins, 'sensors': {}}
    kernel = WORKSPACE / '2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
    support = []
    for relative, expected in SUPPORT_PINS.items():
        p = kernel / relative
        raw = p.read_bytes()
        assert sha(raw) == expected, f'Supporting source changed: {p}'
        destination = SPIKE / 'inputs' / ('COPYING.kernel' if relative == 'COPYING' else p.name)
        destination.write_bytes(raw)
        entry = {'source': str(p.relative_to(WORKSPACE)), 'sha256': expected, 'bytes': len(raw),
                 'copy': str(destination.relative_to(SPIKE))}
        if p.name == 'kd_imgsensor_define.h':
            text = raw.decode()
            match = re.search(r'typedef struct\s*\{\s*MUINT16 full_w;.*?\}\s*SENSOR_WINSIZE_INFO_STRUCT;', text, re.S)
            assert match
            assert re.findall(r'MUINT16\s+(\w+);', match[0]) == WIN_FIELDS
            entry['winsize_type'] = receipt(text, match.span(), str(p.relative_to(WORKSPACE)))
        support.append(entry)
    result['supporting_sources'] = support
    for pin in pins:
        name = Path(pin['path']).name
        if name.endswith('.c'):
            sensor = name[:6]
            result['sensors'][sensor] = extract_sensor(sensor, pin)
        else:
            (SPIKE / 'inputs' / name).write_bytes((WORKSPACE / pin['path']).read_bytes())
    dump(SPIKE / 'evidence/extraction.json', result)
    dump(SPIKE / 'evidence/exact-source-receipts.json', {
         'parent_pin_file': str(PIN_PATH.relative_to(WORKSPACE)), 'parent_pin_file_sha256': sha(PIN_PATH.read_bytes()),
         'four_original_files': pins, 'supporting_sources': support,
         'function_receipts': {s: d['functions'] for s,d in result['sensors'].items()},
         'type_receipts': {s: d['types'] for s,d in result['sensors'].items()},
         'policy': 'Whole public originals copied verbatim with notices, never compiled as drivers; byte-exact whitelisted functions compiled with explicit host fixtures. No source default body executed.'})
    print('Pinned four files verified; extracted and audited mode/scenario/timing bodies for both fitted sensors.')


if __name__ == '__main__':
    main()
