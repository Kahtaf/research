import copy
import hashlib
import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / 'scripts'))
from extract import EXPECTED, WORKSPACE, function, receipt, sha, validate_pins
from facts import geometry, registers


def read(name):
    return json.loads((SPIKE / name).read_text())


def trace_digest(traces):
    return sha(json.dumps(traces, sort_keys=True, separators=(',', ':')).encode())


class ProductionWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extraction = read('evidence/extraction.json')
        cls.facts = read('evidence/sensor-facts.json')
        cls.traces = {s: read(f'evidence/{s}-traces.json') for s in ['ov5670','ov2680']}
        cls.index = {s: {t['case']: t for t in ts} for s,ts in cls.traces.items()}

    def test_original_four_source_pins_and_negative_mutation(self):
        pins = validate_pins()
        # Mutation test uses isolated public copies; never changes pinned originals.
        with tempfile.TemporaryDirectory(dir=SPIKE / 'tests') as scratch:
            scratch = Path(scratch)
            for pin in pins:
                p = scratch / pin['path']
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes((WORKSPACE / pin['path']).read_bytes())
            p = scratch / pins[0]['path']
            p.write_bytes(p.read_bytes().replace(b'write_cmos_sensor(0x3808, 0x05)', b'write_cmos_sensor(0x3808, 0x04)', 1))
            with self.assertRaisesRegex(AssertionError, 'source pin mismatch'):
                validate_pins(scratch, pins)
            changed_pins = copy.deepcopy(pins)
            changed_pins[0]['sha256'] = sha(p.read_bytes())
            with self.assertRaisesRegex(AssertionError, 'parent pin changed'):
                validate_pins(scratch, changed_pins)

    def test_byte_exact_functions_and_callsite_receipts(self):
        for sensor, data in self.extraction['sensors'].items():
            text = (WORKSPACE / data['source']).read_text()
            for name, expected in data['functions'].items():
                span = function(text, name)
                body = (SPIKE / f'generated/{sensor}-{name}.inc').read_bytes()
                self.assertEqual(body, text[span[0]:span[1]].encode())
                self.assertEqual(receipt(text, span, data['source']), expected)
            for name, ref in data['types'].items():
                original=(WORKSPACE/ref['source']).read_text()
                exact='\n'.join(original.splitlines()[ref['start_line']-1:ref['end_line']])
                self.assertEqual(sha(exact.encode()), ref['sha256'])
                self.assertIn(exact,(SPIKE/f'generated/{sensor}-types.inc').read_text())
            for trace in self.traces[sensor]:
                for addr,value,line,fn in trace['writes']:
                    self.assertIn(fn, data['functions'])
                    self.assertLessEqual(data['functions'][fn]['start_line'], line)
                    self.assertLessEqual(line, data['functions'][fn]['end_line'])
                    self.assertIn('write_cmos_sensor', text.splitlines()[line-1])
                    self.assertLessEqual(value, 255)

    def test_locked_complete_register_programs_and_mutation_detection(self):
        gold = read('tests/expected-programs.json')
        for s, traces in self.traces.items():
            self.assertEqual(len(traces), gold[s]['cases'])
            self.assertEqual(trace_digest(traces), gold[s]['sha256'])
            bad = copy.deepcopy(traces)
            bad[0]['writes'][0][1] ^= 1
            self.assertNotEqual(trace_digest(bad), gold[s]['sha256'])

    def test_capture_all_predicate_sides_and_fallbacks(self):
        for s in self.traces:
            for fps in [0,149,150,151,239,240,241,300,65535]:
                t = self.index[s][f'capture/{fps}']
                r = registers(t)
                g = geometry(t)
                if s == 'ov5670':
                    self.assertEqual(g['hts']['value'], 3352 if fps == 150 else 1676)
                    self.assertEqual(r[0x0303]['value'], 1 if fps == 150 else 0)
                    self.assertEqual(g['output_width']['value'], 2592)
                    self.assertEqual(g['vts']['value'], 2045)
                else:
                    self.assertEqual(g['hts']['value'], 1700)
                    self.assertEqual(g['vts']['value'], 1294)
                    self.assertEqual(g['output_width']['value'], 1600)
                    self.assertEqual(t['writes'], self.index[s]['capture/300']['writes'])

    def test_video_parameter_does_not_select_another_program(self):
        for s in self.traces:
            base = self.index[s]['video/0']['writes']
            for fps in [150,240,65535]:
                self.assertEqual(self.index[s][f'video/{fps}']['writes'], base)

    def test_geometry_compares_to_source_tables_without_equating_grab(self):
        for s,facts in self.facts['sensors'].items():
            for row in facts['scenario_programs']:
                c = row['comparison']
                self.assertTrue(c['timing_equals_declared'])
                self.assertTrue(c['output_equals_winsize_stage1'])
                self.assertTrue(c['grab_equals_winsize_target'])
                self.assertEqual(c['output_equals_grab'], s == 'ov2680')
                self.assertFalse(c['android_active_array_resolved'])
        high = next(r for r in self.facts['sensors']['ov5670']['scenario_programs'] if r['declared_mode'] == 'hs_video')
        self.assertEqual(high['comparison']['programmed_output'], [644,480])
        self.assertEqual(high['comparison']['declared_grab_window'], [640,480])

    def test_unknown_registers_stay_unknown_through_transitions(self):
        for s,traces in self.traces.items():
            for t in traces:
                if not t['writes']:
                    continue
                g = geometry(t)
                self.assertIsNone(g['crop_x_start']['value'])
                self.assertIsNone(g['crop_y_start']['value'])
                if s == 'ov5670':
                    self.assertIsNone(g['crop_x_end']['value'])
                    self.assertIsNone(g['crop_y_end']['value'])
                else:
                    self.assertEqual(g['crop_x_start']['unknown_registers'], ['0x3800'])
                    self.assertEqual(g['crop_y_start']['unknown_registers'], ['0x3802'])

    def test_ov2680_240_rate_state_is_not_register_application(self):
        i = self.index['ov2680']
        scenario = i['capture-then-scenario-rate/240']
        applied = i['capture-then-video-rate/240']
        self.assertEqual(scenario['state']['frame_length'], 1617)
        self.assertEqual(len(scenario['writes']), scenario['stage_boundary'])
        self.assertEqual(geometry(scenario)['vts']['value'], 1294)
        self.assertEqual(geometry(applied)['vts']['value'], 1617)
        self.assertEqual(len(applied['writes']) - applied['stage_boundary'], 4)
        self.assertEqual(Fraction(66000000,1700*1617), Fraction(220000,9163))

    def test_framerate_setter_rounding_clamps_and_flicker_branches(self):
        for s,index in self.index.items():
            for fps,want in [(150,146),(300,296),(240,240)]:
                t = index[f'flicker-video-rate/{fps}']
                self.assertEqual(t['state']['current_fps'], want)
                self.assertEqual(geometry(t)['vts']['value'], t['state']['frame_length'])
            for name in ['flicker-video-rate/0','video-scenario-rate-zero']:
                t=index[name]
                self.assertEqual(len(t['writes']), t['stage_boundary'])
            for minimum_en in [0,1]:
                t=index[f'direct-rate/1/{minimum_en}']
                self.assertEqual(geometry(t)['vts']['value'], 32767)
                self.assertEqual(t['state']['frame_length'],32767)
                self.assertEqual(t['state']['min_frame_length'],32767 if minimum_en else (2045 if s=='ov5670' else 1294))

    def test_custom1_mapping_and_missing_default_are_flagged(self):
        d=self.extraction['sensors']['ov5670']
        self.assertEqual(len(d['winsize']),6)
        self.assertFalse(any('MSDK_SCENARIO_ID_CUSTOM1' in m['labels'] for m in d['crop_dispatch']['mapping']))
        self.assertEqual(self.index['ov5670']['default-rate/CUSTOM1']['default_rate_query'],99999)
        findings=self.facts['sensors']['ov5670']['findings']
        self.assertEqual(sum(x['kind']=='incomplete_mapping' for x in findings),2)
        for s in self.traces:
            self.assertEqual(self.index[s]['invalid-scenario']['status'],77)
            preview=next(t for t in self.traces[s] if t['case'].startswith('control/CAMERA_PREVIEW'))
            self.assertEqual(self.index[s]['invalid-scenario']['writes'], preview['writes'])

    def test_rationals_are_exact_and_rate_claims_remain_separate(self):
        for s,data in self.facts['sensors'].items():
            for row in data['scenario_programs']:
                fields=data['declared_modes'][row['declared_mode']]['fields']
                pclk=fields['pclk']['value'];g=row['geometry']
                r=row['source_clock_over_programmed_timing_hz']
                self.assertEqual(Fraction(r['numerator'],r['denominator']),Fraction(pclk,g['hts']['value']*g['vts']['value']))
                self.assertIsInstance(r['numerator'],int)
        cap1=next(r for r in self.facts['sensors']['ov2680']['scenario_programs'] if r['declared_mode']=='cap1')
        self.assertEqual(cap1['declared_max_framerate_tenths']['value'],240)
        self.assertNotEqual(cap1['source_clock_over_programmed_timing_hz'],cap1['declared_rate_hz'])

    def test_sdk37_coverage_does_not_emit_contract_or_templates(self):
        c=read('evidence/metadata-input-coverage.json')
        self.assertEqual(len(c['templates']),6)
        for entry in c['templates']:
            self.assertIsNone(entry['supported'])
            self.assertFalse(entry['request_template_emitted'])
            ref=entry['schema']
            self.assertIn(ref['token'],(WORKSPACE/ref['source']).read_text().splitlines()[ref['line']-1])
        for entry in c['characteristics_and_request_categories']:
            self.assertFalse(entry['metadata_values_emitted'])
            for ref in entry['sdk37_tokens']:
                self.assertIn(ref['token'],(WORKSPACE/ref['source']).read_text().splitlines()[ref['line']-1])
        for s,d in self.extraction['sensors'].items():
            self.assertFalse(d['defaults_executed'])
            self.assertNotIn('sensor_init',d['functions'])
            self.assertNotIn('read_cmos_sensor',d['functions'])


if __name__ == '__main__':
    unittest.main()
