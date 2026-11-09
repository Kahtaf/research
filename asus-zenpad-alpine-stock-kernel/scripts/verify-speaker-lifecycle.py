#!/usr/bin/env python3
"""Two bounded quiet browser episodes; no persistent route installation."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prototype-sha256', required=True)
args = parser.parse_args()
PROTO = Path('/tmp/asus-speaker-route-prototype.py')
MEDIA = Path('/tmp/asus-speaker-lifecycle-sound.m4a')
ROOT = Path('/run/asus-speaker-lifecycle')
ROUTE = Path('/run/asus-goodix-audio')
PCM = Path('/proc/asound/card0/pcm0p/sub0/hw_params')
AMPS = ('Ext_Speaker_Amp_Switch', 'Speaker_Amp_Switch')
GAIN, CLASS = 'Audio_Speaker_PGA_gain', 'Audio_Speaker_class_Switch'
os.environ.update(DISPLAY=':0', XAUTHORITY='/run/asus-goodix/Xauthority', XDG_RUNTIME_DIR='/run/user/0')
assert hashlib.sha256(PROTO.read_bytes()).hexdigest() == args.prototype_sha256
assert hashlib.sha256(MEDIA.read_bytes()).hexdigest() == '2b304ffa302593d2bd2df9f0164f59ceba408f777247ce78a7d41a3cd0fe8888'
assert not ROOT.exists()
ROOT.mkdir(mode=0o700)
pulse = json.loads((ROUTE/'state.json').read_text())


def stamp(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def control(name):
    text = subprocess.check_output(['amixer', '-c', '0', 'cget', 'name='+name], text=True, timeout=1)
    return int(re.search(r'^\s*: values=(\d+)$', text, re.M)[1])


def restored():
    assert all(control(n) == 0 for n in AMPS)
    assert control(GAIN) == baseline['gain'] and control(CLASS) == baseline['class']
    assert not (ROUTE/'route-preimage.json').exists()
    fd = os.open(ROUTE/'route.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(fd)  # Last close releases this separate probe description.


def idle():
    deadline = time.monotonic()+12
    while time.monotonic() < deadline:
        if PCM.read_text().strip() == 'closed':
            text = subprocess.check_output(['/usr/local/bin/asus-goodix-audio', 'status'], text=True, timeout=2)
            assert text.strip().endswith('SUSPENDED'), text
            return
        time.sleep(.05)
    raise RuntimeError('Sink did not become idle/closed')


def read_events(directory):
    path = directory/'events.jsonl'
    if not path.exists():
        return []
    lines = path.read_text().splitlines(keepends=True)
    return [json.loads(line) for line in lines if line.endswith('\n')]


def stop_controller(status):
    pid = status['controller_pid']
    if stamp(pid) == status['controller_start']:
        assert int(Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[1]) == status['guardian_pid']
        os.kill(pid, signal.SIGTERM)


assert stamp(pulse['pid']) == pulse['start']
idle()
baseline = {'class': control(CLASS), 'gain': control(GAIN)}
restored()
server = None
current = None
receipt = {'baseline': baseline, 'episodes': [], 'physical_audibility': 'unconfirmed'}
try:
    with (ROOT/'web.log').open('wb') as log:
        server = subprocess.Popen(['python3', '/tmp/asus-speaker-lifecycle-fixture.py', '--media', str(MEDIA), '--state', str(ROOT/'web')],
                                  stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(40):
        assert server.poll() is None
        try:
            urllib.request.urlopen('http://127.0.0.1:8088/state', timeout=.5)
            break
        except OSError:
            time.sleep(.1)
    else:
        raise RuntimeError('Fixture server not ready')
    subprocess.run(['python3', '/usr/local/bin/goodix-open-url.py', 'http://127.0.0.1:8088/', '--expect-title', 'ASUS speaker lifecycle software check'], check=True, timeout=35)
    for _ in range(50):
        web = json.loads((ROOT/'web/state.json').read_text())
        if any(e['event'] == 'ready' for e in web['events']):
            break
        time.sleep(.1)
    else:
        raise RuntimeError('Browser fixture not ready')
    for number, label in enumerate(('normal', 'stopped-controller'), 1):
        idle()
        restored()
        episode = ROOT/label
        episode.mkdir(mode=0o700)
        with (ROOT/(label+'.log')).open('wb') as log:
            current = subprocess.Popen(['python3', str(PROTO), '--episode-dir', str(episode), '--cap-seconds', '6'],
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            assert current.poll() is None, (episode, 'Prototype exited before READY')
            status = json.loads((episode/'status.json').read_text()) if (episode/'status.json').exists() else {}
            if status.get('phase') == 'READY':
                break
            assert status.get('phase') != 'ERROR', status
            time.sleep(.01)
        else:
            raise RuntimeError('Prototype not ready')
        subprocess.run(['xdotool', 'key', 'Return'], check=True, timeout=1)
        stopped_at = None
        off_event = None
        while current.poll() is None:
            events = read_events(episode)
            if label == 'stopped-controller' and stopped_at is None and any(e['event'] == 'on_verified' for e in events):
                status = json.loads((episode/'status.json').read_text())
                pid = status['controller_pid']
                assert stamp(pid) == status['controller_start'] and os.getpgid(pid) == pid
                stopped_at = time.monotonic()
                os.kill(pid, signal.SIGSTOP)
            if label == 'normal':
                off_event = next((e for e in events if e['event'] == 'off_verified' and e['reason'] == 'IDLE'), None)
                if off_event:
                    status = json.loads((episode/'status.json').read_text())
                    stop_controller(status)
                    break
            status = json.loads((episode/'status.json').read_text())
            assert status['phase'] != 'ERROR', status
            assert time.monotonic() < deadline+8, 'Prototype exceeded cleanup deadline'
            time.sleep(.01)
        assert current.wait(timeout=4) == 0
        status = json.loads((episode/'status.json').read_text())
        events = read_events(episode)
        assert status['phase'] == 'DONE', status
        on = next(e for e in events if e['event'] == 'on_verified')
        on_begin = next(e for e in events if e['event'] == 'on_begin')
        on_writes = [e['control'] for e in events if e['event'] == 'control_write'
                     and on_begin['monotonic'] <= e['monotonic'] <= on['monotonic']]
        assert on_writes == [GAIN, CLASS, 'Speaker_Amp_Switch', 'Ext_Speaker_Amp_Switch'], on_writes
        assert all(e['monotonic']-status['ready_monotonic'] <= 6 for e in events if e['event'] == 'off_verified')
        if label == 'normal':
            assert off_event and off_event['pcm_open']
            observed_idle = next(e for e in reversed(events) if e['event'] == 'sink_state' and e['state'] == 'IDLE' and e['monotonic'] <= off_event['monotonic'])
            assert off_event['monotonic']-observed_idle['monotonic'] <= 1.5
            assert status['outcome'] == 'controller_eof', status
        else:
            expiry = next(e for e in events if e['event'] == 'heartbeat_expired')
            assert stopped_at is not None and 2.3 <= expiry['monotonic']-stopped_at <= 3.5
            assert 2.5 <= expiry['heartbeat_age'] <= 3.5
            assert status['outcome'] == 'heartbeat_expired'
            assert any(e['event'] == 'descendants_reaped' and e['descendants'] for e in events)
        off = next(e for e in events if e['event'] == 'off_verified' and e['monotonic'] > on['monotonic'])
        off_begin = next(e for e in events if e['event'] == 'off_begin' and e['monotonic'] > on['monotonic'])
        off_writes = [e['control'] for e in events if e['event'] == 'control_write'
                      and off_begin['monotonic'] <= e['monotonic'] <= off['monotonic']]
        assert off_writes == list(AMPS), off_writes
        restored_event = next(e for e in events if e['event'] == 'restore_verified')
        assert restored_event['monotonic'] > off['monotonic']
        assert restored_event['gain'] == baseline['gain'] and restored_event['speaker_class'] == baseline['class']
        for proc in Path('/proc').iterdir():
            if not proc.name.isdecimal():
                continue
            try:
                assert int((proc/'stat').read_text().rsplit(')', 1)[1].split()[2]) != status['controller_pid'], 'Controller process group survived'
            except FileNotFoundError:
                pass
        restored()
        web = json.loads((ROOT/'web/state.json').read_text())
        end_deadline = time.monotonic()+5
        while not any(e['episode'] == number and e['event'] == 'ended' for e in web['events']):
            assert time.monotonic() < end_deadline, 'Browser playback did not end'
            assert not any(e['event'] in ('error', 'play-rejected') for e in web['events'])
            time.sleep(.05)
            web = json.loads((ROOT/'web/state.json').read_text())
        ended = next(e for e in web['events'] if e['episode'] == number and e['event'] == 'ended')
        assert ended['time'] >= 3 and ended['error'] is None and not ended['muted'] and ended['volume'] == .05
        idle()
        assert stamp(pulse['pid']) == pulse['start']
        receipt['episodes'].append({'name': label, 'outcome': status['outcome'], 'browser_ended': ended, 'status': status,
                                    'on_order': on_writes, 'off_order': off_writes, 'off_pcm_open': off['pcm_open'],
                                    'gate_off_seconds_after_ready': off['monotonic']-status['ready_monotonic'],
                                    'shutdown_seconds_after_observed_idle': off['monotonic']-observed_idle['monotonic'] if label == 'normal' else None,
                                    'expiry_seconds_after_sigstop': expiry['monotonic']-stopped_at if label != 'normal' else None})
        current = None
    assert 'Internal error: Oops' not in subprocess.check_output(['dmesg'], text=True)
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        try:
            command = (proc/'cmdline').read_bytes().split(b'\0')
            if command and command[0] == b'/usr/lib/firefox-esr/firefox-esr':
                assert '/dev/snd/pcm' not in (proc/'maps').read_text()
                for descriptor in (proc/'fd').iterdir():
                    try:
                        assert '/dev/snd/pcm' not in str(descriptor.readlink())
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
    receipt.update(status='NORMAL_AND_SIGSTOP_CLEANUP_PASS', pulse_daemon_unchanged=True, final_pcm='closed', final_amps=[control(n) for n in AMPS])
    (ROOT/'result.json').write_text(json.dumps(receipt)+'\n')
    print('SPEAKER_LIFECYCLE_RESULT', json.dumps(receipt), flush=True)
finally:
    if current is not None and current.poll() is None:
        status = json.loads((episode/'status.json').read_text())
        if status.get('controller_pid'):
            try:
                stop_controller(status)
            except FileNotFoundError:
                pass
        # Never kill the guardian: it owns safety cleanup and any ERROR lock.
        try:
            current.wait(timeout=8)
        except subprocess.TimeoutExpired:
            print('GUARDIAN_STILL_OWNS_ROUTE; inspect exact episode state', flush=True)
    subprocess.run(['python3', '/usr/local/bin/goodix-open-url.py', 'http://127.0.0.1:8080/'], check=True, timeout=35)
    if (ROOT/'web').exists():
        (ROOT/'web/STOP').touch()
