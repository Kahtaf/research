"""Independent tests of the pinned dispatch fix; no external transport."""
import ast
import dataclasses
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RECORDS = []

def configure(module):
    global m, t
    m, t = module, module.t
    for name in ('setUp', 'tearDown', 'mode', 'calls', 'events', 'observe', 'direct'):
        setattr(IndependentCases, name, getattr(m.Cases, name))
    IndependentCases.setUpClass = classmethod(m.Cases.setUpClass.__func__)

class IndependentCases(unittest.TestCase):
    def record(self, **value):
        RECORDS.append(dict(test=self.id(), source_sha256=self.source_sha, **value))
        (ROOT/'evidence/independent-results.json').write_text(json.dumps(RECORDS, indent=2)+'\n')

    def refused(self, *, stage='writable', wall=1.5, mono=1.5, epoch=False, deadline=False):
        real_wall, real_mono, real_write = time.time, time.monotonic, os.write
        original_events = t.PipeStream._events
        original_epoch = self.deployment.host_clock_epoch
        delta = 0.0
        probes = 0
        writes = []
        gates = []
        old = self.binding
        if not deadline:
            self.binding = dataclasses.replace(old, created_wall=real_wall()-179, created_monotonic=real_mono()-179)
        def probe(end):
            nonlocal probes, delta
            probes += 1
            if stage == 'probe' and probes == 6:
                delta = 1.0
        def events(child):
            nonlocal delta
            ready = original_events(child)
            if stage == 'writable' and child.before_write.__name__ == 'dispatch_fresh' and any(k.data=='stdin' for k,_ in ready):
                delta = 1.0
            return ready
        def write(fd, data):
            # Only observe the actual request stream; discovery children write in their own processes.
            writes.append(bytes(data).hex())
            return real_write(fd, data)
        def host_epoch():
            value = original_epoch()
            return value+'-changed' if epoch and delta else value
        check = t.check_binding
        def binding_gate(binding, value):
            gates.append(dict(wall_age=time.time()-binding.created_wall,
                              monotonic_age=time.monotonic()-binding.created_monotonic,
                              changed_epoch=epoch and bool(delta)))
            return check(binding, value)
        with patch.object(time,'time',side_effect=lambda:real_wall()+delta*wall), \
             patch.object(time,'monotonic',side_effect=lambda:real_mono()+delta*mono), \
             patch.object(t,'server_version',side_effect=probe), \
             patch.object(t.PipeStream,'_events',events), \
             patch.object(self.deployment,'host_clock_epoch',side_effect=host_epoch), \
             patch.object(t,'check_binding',side_effect=binding_gate), \
             patch.object(os,'write',side_effect=write):
            with self.assertRaises(t.Refused):
                self.observe()
        self.assertEqual(probes, 6)
        self.assertFalse(writes)
        self.assertFalse((self.d/'request.bin').exists())
        self.assertEqual(self.events()[-1]['result'], 'UNKNOWN')
        before = len(self.children)
        with self.assertRaises(FileExistsError):
            self.observe()
        self.assertEqual(len(self.children), before)
        self.record(stage=stage, probes=probes, request_write_attempts=0, terminal='UNKNOWN',
                    retry_new_children=0, last_gate=gates[-1], wall_delta=wall, mono_delta=mono,
                    epoch_changed=epoch, original_deadline_expired=deadline)

    def test_old_p1_slow_final_probe(self):
        self.refused(stage='probe')

    def test_old_p1_delayed_writable_event(self):
        self.refused()

    def test_wall_only_expiry_at_writable_event(self):
        self.refused(mono=0)

    def test_monotonic_only_expiry_at_writable_event(self):
        self.refused(wall=0)

    def test_wall_backward_to_future_binding(self):
        self.refused(wall=-181, mono=0)

    def test_monotonic_backward_to_future_binding(self):
        self.refused(wall=0, mono=-181)

    def test_current_epoch_change_at_write_boundary(self):
        self.refused(wall=0, mono=0, epoch=True)

    def test_original_whole_deadline_checked_after_wait(self):
        self.refused(wall=0, mono=11, deadline=True)

    def write_scenario(self, kind):
        original_write, original_events = os.write, t.PipeStream._events
        real_wall, real_mono = time.time, time.monotonic
        offset = 0.0
        attempts, committed, ordering = [], bytearray(), []
        gate_count = 0
        if kind.endswith('expiry'):
            self.binding = dataclasses.replace(self.binding, created_wall=real_wall()-179,
                                              created_monotonic=real_mono()-179)
        def events(child):
            ready = original_events(child)
            if child.before_write.__name__ == 'dispatch_fresh':
                ordering.append('events')
            return ready
        original_binding = t.check_binding
        def binding_check(binding, epoch):
            nonlocal gate_count
            gate_count += 1
            ordering.append('gate')
            return original_binding(binding, epoch)
        def write(fd, data):
            nonlocal offset
            value = bytes(data)
            attempts.append(dict(bytes=len(value), gates=gate_count, previous=ordering[-1]))
            self.assertEqual(ordering[-1], 'gate')
            if len(attempts) == 1 and kind.startswith('eagain'):
                if kind.endswith('expiry'):offset = 1.5
                raise BlockingIOError('owned EAGAIN')
            if len(attempts) == 1 and kind.startswith('partial'):
                n = original_write(fd, value[:7]);committed.extend(value[:n])
                if kind.endswith('expiry'):offset = 1.5
                return n
            n = original_write(fd, value);committed.extend(value[:n]);return n
        with patch.object(os,'write',side_effect=write), \
             patch.object(t.PipeStream,'_events',events), \
             patch.object(t,'check_binding',side_effect=binding_check), \
             patch.object(time,'time',side_effect=lambda:real_wall()+offset), \
             patch.object(time,'monotonic',side_effect=lambda:real_mono()+offset):
            if kind.endswith('expiry'):
                with self.assertRaises(t.Refused):self.observe()
                self.assertEqual(self.events()[-1]['result'],'UNKNOWN')
            else:
                result=self.observe()
                self.assertEqual(result['result'],'OBSERVED_MATCH')
                self.assertEqual(t.accept_completion(self.binding,exit_status=0,stdout=json.dumps(result).encode(),
                                 expected_source_sha256=self.source_sha),result)
        if kind.endswith('expiry'):
            self.assertEqual(len(attempts),1)
            self.assertEqual(len(committed),7 if kind.startswith('partial') else 0)
            self.assertFalse((self.d/'request.bin').exists())
            count=len(self.children)
            with self.assertRaises(FileExistsError):self.observe()
            self.assertEqual(len(self.children),count)
        else:
            self.assertEqual(len(attempts),2)
            self.assertGreater(attempts[1]['gates'],attempts[0]['gates'])
            self.assertEqual(bytes(committed),self.measure.REQUEST)
            self.assertEqual((self.d/'request.bin').read_bytes(),self.measure.REQUEST)
        self.assertEqual(sum('shell' in a for a in self.calls()),1)
        self.record(scenario=kind, attempts=attempts, committed_bytes=len(committed),
                    terminal=self.events()[-1]['result'], shell_children=1)

    def test_eagain_rechecks_and_sends_exactly_one_request(self):self.write_scenario('eagain')
    def test_partial_write_rechecks_and_sends_exactly_one_request(self):self.write_scenario('partial')
    def test_eagain_then_expiry_refuses_zero_committed_bytes(self):self.write_scenario('eagain_expiry')
    def test_partial_write_then_expiry_stops_without_retry(self):self.write_scenario('partial_expiry')

    def test_sendall_is_consumed_even_when_before_send_refuses(self):
        child=self.direct('backpressure',1)
        child.before_send=lambda:(_ for _ in ()).throw(t.Refused('owned guard failure'))
        try:
            with self.assertRaises(t.Refused):child.sendall(self.measure.REQUEST)
            self.assertTrue(child.sent)
            with self.assertRaisesRegex(t.Refused,'Only one request'):child.sendall(self.measure.REQUEST)
        finally:child.dispose()
        self.assertFalse((self.d/'request.bin').exists())

    def test_fresh_dispatch_late_binding_completion_is_accepted(self):
        real_wall,real_mono,real_write=time.time,time.monotonic,os.write
        offset=0.0;sends=[]
        self.binding=dataclasses.replace(self.binding,created_wall=real_wall()-179,created_monotonic=real_mono()-179)
        def write(fd,data):
            nonlocal offset
            sends.append(dict(wall_age=time.time()-self.binding.created_wall,
                              monotonic_age=time.monotonic()-self.binding.created_monotonic))
            n=real_write(fd,data);offset=1.5;return n
        with patch.object(time,'time',side_effect=lambda:real_wall()+offset), \
             patch.object(time,'monotonic',side_effect=lambda:real_mono()+offset), \
             patch.object(os,'write',side_effect=write):
            result=self.observe()
            finish_age=time.monotonic()-self.binding.created_monotonic
            self.assertGreater(finish_age,180)
            self.assertEqual(t.accept_completion(self.binding,exit_status=0,stdout=json.dumps(result).encode(),
                             expected_source_sha256=self.source_sha),result)
        self.assertEqual(len(sends),1)
        self.assertTrue(all(0<=age<=180 for age in sends[0].values()))
        self.assertEqual((self.d/'request.bin').read_bytes(),self.measure.REQUEST)
        self.record(dispatch_ages=sends[0],finish_monotonic_age=finish_age,terminal=result['result'],accepted=True)

    def test_readme_all_pin_assertions_and_actual_plan(self):
        recipe=(m.ROOT/'README.md').read_text().split('```python\n')[1].split('```')[0]
        nodes=ast.parse(recipe).body
        pins=[n for n in nodes if isinstance(n,ast.Assert) or
              isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='TRANSPORT_SHA' for x in n.targets)]
        self.assertEqual(sum(isinstance(x,ast.Assert) for x in pins),4)
        # Restore documented constant only while evaluating the assertion; never launch it.
        with patch.object(t,'ADB',Path('/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb')):
            exec(compile(ast.Module(body=pins,type_ignores=[]),'<README pins>','exec'),dict(transport=t))
        self.record(readme_assertions_executed=4,source_pin=self.source_sha,observe_recipe_executed=False)
