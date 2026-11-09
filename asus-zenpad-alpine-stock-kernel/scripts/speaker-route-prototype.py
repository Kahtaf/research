#!/usr/bin/env python3
"""One bounded stock-kernel speaker episode; never start PulseAudio or open PCM."""
import argparse
import ctypes
import errno
import fcntl
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import struct
import subprocess
import sys
import time

AMPS = ('Ext_Speaker_Amp_Switch', 'Speaker_Amp_Switch')
OTHER_AMPS = ('Audio_Amp_L_Switch', 'Audio_Amp_R_Switch',
              'Headset_Speaker_Amp_Switch', 'Voice_Amp_Switch')
GAIN, CLASS = 'Audio_Speaker_PGA_gain', 'Audio_Speaker_class_Switch'
COMMAND_TIMEOUT = .25
HEARTBEAT_TIMEOUT = 2.5
OFF_RESERVE = 1.1  # Four bounded set/readback calls, plus scheduling margin.
PCM = Path('/proc/asound/card0/pcm0p/sub0/hw_params')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def prctl(option, value):
    libc = ctypes.CDLL(None, use_errno=True)
    require(sys.platform == 'linux', 'Linux process contracts required')
    if libc.prctl(option, value, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'prctl failed')


def stamp(pid):
    fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    return fields[19]


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def private_dir(path):
    require(path.is_absolute() and path.resolve() == path, 'Canonical absolute directory required')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and info.st_mode & 0o077 == 0,
            'Directory must be root owned and private')
    mounts = [line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    enclosing = [m for m in mounts if path == Path(m[4]) or Path(m[4]) in path.parents]
    mount = max(enclosing, key=lambda m: len(m[4]))
    require(mount[mount.index('-')+1] == 'tmpfs', 'State must be on RAM tmpfs')


def identity():
    require(os.geteuid() == 0 and os.uname().release == '3.18.35', 'Wrong kernel/root identity')
    require(Path('/etc/asus-alpine-ram-release').read_text().strip() ==
            'asus-alpine-stock-kernel-v1', 'Wrong Alpine root marker')
    loop = Path('/run/asus-alpine/root-loop-device').read_text().strip()
    require(loop == 'loop0', 'Unexpected recorded root loop device')
    dev = Path('/sys/block', loop, 'dev').read_text().strip()
    major, minor = map(int, dev.split(':'))
    root_dev = os.makedev(major, minor)
    alias = Path('/dev/asus-alpine-root-loop').stat()
    require(stat.S_ISBLK(alias.st_mode) and alias.st_rdev == root_dev and
            os.stat('/').st_dev == root_dev, 'Root is not the recorded SD loop device')
    mounts = [line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    require(any(m[2] == dev and m[4] == '/' and m[m.index('-')+1] == 'ext4' for m in mounts),
            'Root ext4 mount identity missing')
    backing = Path('/sys/block', loop, 'loop/backing_file').read_text().strip()
    require(backing.lstrip('/') == 'mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4',
            'Wrong SD root backing file')
    require(Path('/proc/asound/card0/id').read_text().strip() == 'mtsndcard', 'Wrong ALSA card')
    codecs = [p for p in Path('/proc/device-tree').rglob('compatible')
              if b'mediatek,mt8163-soc-codec-63xx\0' in p.read_bytes()]
    require(len(codecs) == 1, 'Wrong loaded codec')
    gpio = (codecs[0].parent/'extspkamp-gpio').read_bytes()
    require(len(gpio) == 12 and struct.unpack('>III', gpio)[1:] == (28, 0), 'Wrong amplifier GPIO')


def atomic_json(path, data):
    temporary = path.with_name(path.name+'.'+str(os.getpid())+'.new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(data, output, sort_keys=True)
        output.write('\n')
    temporary.replace(path)


class Episode:
    def __init__(self, args):
        self.args = args
        self.lock = None
        self.locked = False
        self.pipe = None
        self.stop = False
        self.on = False
        self.ready_at = None
        self.status = {'guardian_pid': os.getpid(), 'guardian_start': stamp(os.getpid()),
                       'controller_pid': None, 'controller_start': None,
                       'boot_id': boot_id(), 'phase': 'STARTING', 'ready': False,
                       'ready_monotonic': None, 'cap_monotonic': None,
                       'cleanup_monotonic': None}
        self.events = os.open(args.episode_dir/'events.jsonl',
                              os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        self.preimage = args.route_root/'route-preimage.json'

    def event(self, event, **details):
        data = {'event': event, 'pid': os.getpid(), 'monotonic': time.monotonic(),
                'wall_time': time.time(), **details}
        os.write(self.events, (json.dumps(data, sort_keys=True)+'\n').encode())

    def phase(self, phase, **details):
        self.status.update(phase=phase, **details)
        atomic_json(self.args.episode_dir/'status.json', self.status)

    def beat(self):
        if self.pipe is not None:
            os.write(self.pipe, b'.\n')

    def run(self, argv, *, env=None, writer=False):
        # Writers retain the SAME flock description even if both Python processes die.
        child = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 close_fds=True, pass_fds=(self.lock,) if writer else ())
        try:
            stdout, _ = child.communicate(timeout=COMMAND_TIMEOUT)
            require(child.returncode == 0, 'Subprocess failed: '+argv[0])
            return stdout.decode()
        except BaseException:
            child.kill()
            child.wait()  # Never write cleanup while a timed-out writer survives.
            raise
        finally:
            self.beat()

    def control(self, name):
        raw = self.run(['amixer', '-c', '0', 'cget', 'name='+name])
        match = re.search(r'^\s*: values=(\d+)$', raw, re.M)
        require(match is not None, 'Unknown mixer readback')
        value = int(match[1])
        self.event('control_read', control=name, value=value, raw=raw)
        return value, raw

    def set_control(self, name, value, turning_on=False):
        if turning_on:
            require(not self.stop and time.monotonic() < self.ready_at+self.args.cap_seconds-OFF_RESERVE,
                    'Episode stopping')
        self.event('control_write', control=name, value=value)
        self.run(['amixer', '-q', '-c', '0', 'cset', 'name='+name, str(value)], writer=True)
        require(self.control(name)[0] == value, 'Mixer readback mismatch: '+name)

    def off(self, reason):
        self.event('off_begin', reason=reason, pcm_open=PCM.read_text().strip() != 'closed')
        # Speaker Off follows confirmed Ext Off; class restoration follows both.
        for name in AMPS:
            self.set_control(name, 0)
        self.on = False
        self.event('off_verified', reason=reason, pcm_open=PCM.read_text().strip() != 'closed')
        self.phase('OFF')

    def restore(self, saved):
        require(all(self.control(n)[0] == 0 for n in AMPS), 'Do not restore through powered gates')
        self.set_control(CLASS, saved['class'])
        self.set_control(GAIN, saved['gain'])
        self.event('restore_verified', gain=saved['gain'], speaker_class=saved['class'])
        self.preimage.unlink(missing_ok=True)
        self.event('preimage_deleted')

    def load_audio(self):
        loader = importlib.machinery.SourceFileLoader('owned_goodix_audio', '/usr/local/bin/asus-goodix-audio')
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.audio = importlib.util.module_from_spec(spec)
        loader.exec_module(self.audio)
        require(self.audio.RUN == self.args.route_root, 'Audio helper route root differs')
        require(Path('/etc/asound.conf').read_text() == self.audio.GUARD, 'ALSA guard changed')
        self.pulse = json.loads((self.args.route_root/'state.json').read_text())
        require(set(self.pulse) == {'pid', 'start', 'boot_id'} and type(self.pulse['pid']) is int,
                'Unexpected PulseAudio identity schema')
        # Reuse the actual verify_sink/owned functions, imposing our tighter timeout
        # without changing the process-global subprocess module or installed helper.
        episode = self
        class BoundedCommands:
            @staticmethod
            def check_output(argv, *, env=None, text=False, timeout=None):
                result = episode.run(argv, env=env)
                return result if text else result.encode()
        self.audio.subprocess = BoundedCommands
        self.audio.verify_sink(self.pulse)

    def validate_saved(self, saved):
        require(set(saved) == {'schema', 'boot_id', 'guardian', 'pulse', 'class', 'gain'},
                'Unexpected preimage schema')
        require(saved['schema'] == 1 and saved['boot_id'] == boot_id(), 'Stale preimage boot')
        require(saved['pulse'] == self.pulse and self.audio.owned(saved['pulse']), 'Stale preimage PulseAudio')
        owner = saved['guardian']
        require(set(owner) == {'pid', 'start'} and type(owner['pid']) is int and owner['pid'] > 1
                and isinstance(owner['start'], str) and owner['start'].isdigit(), 'Invalid guardian identity')
        require(self.audio.process_start(owner['pid']) != owner['start'], 'Prior guardian still alive')
        for name, value in ((CLASS, saved['class']), (GAIN, saved['gain'])):
            require(type(value) is int and f"Item #{value} '" in self.control(name)[1], 'Invalid saved control')
        require(saved['gain'] > 0, 'Mute gain cannot be restored faithfully')

    def prepare(self):
        self.lock = os.open(self.args.route_root/'route.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        info = os.fstat(self.lock)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                and info.st_mode & 0o077 == 0, 'Unsafe route lock')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.locked = True
        self.event('lock_acquired')
        try:
            self.load_audio()
        except Exception:
            if any(self.control(n)[0] != 0 for n in AMPS):
                self.off('audio_validation_failed')
            raise
        if self.preimage.exists() or self.preimage.is_symlink():
            try:
                require(not self.preimage.is_symlink(), 'Symlink preimage')
                saved = json.loads(self.preimage.read_text())
                self.validate_saved(saved)
            except Exception:
                self.off('invalid_preimage')
                raise
            self.off('leftover_preimage')
            self.restore(saved)
            self.event('leftover_recovered')
        elif any(self.control(n)[0] != 0 for n in AMPS):
            self.off('unowned_powered_gates')
            raise RuntimeError('Powered gates without preimage; class/gain left untouched')
        require(self.audio.verify_sink(self.pulse) == 'SUSPENDED' and PCM.read_text().strip() == 'closed',
                'Start requires SUSPENDED and PCM closed')
        for name in AMPS+OTHER_AMPS:
            require(self.control(name)[0] == 0, 'Analog route already powered')
        gain, gain_raw = self.control(GAIN)
        cls, class_raw = self.control(CLASS)
        require("Item #1 '0Db'" in gain_raw and "Item #1 'CLASSAB'" in class_raw,
                'Unexpected route enumerations')
        require(gain > 0, 'Mute gain cannot be restored faithfully')
        self.saved = {'schema': 1, 'boot_id': boot_id(),
                      'guardian': {'pid': os.getpid(), 'start': stamp(os.getpid())},
                      'pulse': self.pulse, 'class': cls, 'gain': gain}
        atomic_json(self.preimage, self.saved)
        self.event('preimage_saved', gain=gain, speaker_class=cls)

    def turn_on(self):
        self.event('on_begin')
        self.set_control(GAIN, 1, True)
        self.set_control(CLASS, 1, True)
        self.set_control('Speaker_Amp_Switch', 1, True)
        self.set_control('Ext_Speaker_Amp_Switch', 1, True)
        time.sleep(.025)
        self.on = True
        self.event('on_verified')
        self.phase('ON')

    def controller(self, guardian, pipe):
        self.pipe = pipe
        os.setpgid(0, 0)
        prctl(1, signal.SIGKILL)  # PR_SET_PDEATHSIG
        require(os.getppid() == guardian, 'Guardian died before controller setup')
        self.status.update(controller_pid=os.getpid(), controller_start=stamp(os.getpid()))
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: setattr(self, 'stop', True))
        subscriber = subprocess.Popen(['pactl', 'subscribe'], env=self.audio.ENV,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, close_fds=True)
        os.set_blocking(subscriber.stdout.fileno(), False)
        buffered = b''

        def events(timeout):
            nonlocal buffered
            relevant, client = False, False
            if select.select([subscriber.stdout], [], [], timeout)[0]:
                data = os.read(subscriber.stdout.fileno(), 65536)
                require(data, 'Subscription EOF')
                buffered += data
                while b'\n' in buffered:
                    line, buffered = buffered.split(b'\n', 1)
                    relevant |= b' on sink #' in line
                    client |= b' on client #' in line
            self.beat()
            return relevant, client

        success = False
        try:
            # Each query connects a client after subscribe. A client event proves
            # subscription registration; a final level query closes remaining races.
            for _ in range(3):
                self.run(['pactl', 'list', 'sinks', 'short'], env=self.audio.ENV)
                if events(.2)[1]:
                    break
            else:
                raise RuntimeError('Subscription startup handshake failed')
            require(not self.stop, 'Interrupted during handshake')
            require(self.audio.verify_sink(self.pulse) == 'SUSPENDED', 'Sink changed before READY')
            self.ready_at = time.monotonic()
            self.status.update(ready=True, ready_monotonic=self.ready_at,
                               cap_monotonic=self.ready_at+self.args.cap_seconds,
                               cleanup_monotonic=self.ready_at+self.args.cap_seconds-OFF_RESERVE)
            self.event('subscription_ready', **{k: self.status[k] for k in
                       ('ready_monotonic', 'cap_monotonic', 'cleanup_monotonic')})
            os.write(pipe, ('R '+str(self.ready_at)+'\n').encode())
            self.phase('READY')
            poll_at = time.monotonic()
            while not self.stop:
                remaining = self.status['cleanup_monotonic']-time.monotonic()
                if remaining <= 0:
                    break
                relevant, _ = events(min(remaining, max(0, poll_at-time.monotonic())))
                if not relevant and time.monotonic() < poll_at:
                    continue
                sink = self.audio.verify_sink(self.pulse)
                self.event('sink_state', state=sink, pcm_open=PCM.read_text().strip() != 'closed')
                require(all(self.control(n)[0] == 0 for n in OTHER_AMPS), 'Another analog route powered')
                if sink == 'RUNNING' and not self.on:
                    require(self.audio.verify_sink(self.pulse) == 'RUNNING', 'Demand changed before On')
                    self.turn_on()
                elif sink != 'RUNNING' and self.on:
                    self.off(sink)
                poll_at = time.monotonic()+1
            if self.on:
                self.off('controller_stop')
            self.restore(self.saved)
            success = True
        except BaseException as error:
            self.event('controller_error', error=type(error).__name__)
            # G owns forced cleanup after killing/reaping every descendant. Do not
            # race its watchdog with a second cleanup sequence after any failure.
        finally:
            subscriber.kill()
            subscriber.wait()
            self.event('controller_exit', clean=success)
            os.close(pipe)
        os._exit(0 if success else 1)

    def kill_and_reap(self, pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            # Before C's setpgid, only C exists. It cannot have spawned a writer.
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        statuses = []
        while True:
            try:
                child, status = os.waitpid(-1, 0)
                statuses.append({'pid': child, 'status': status})
            except ChildProcessError:
                break
            except InterruptedError:
                continue
        self.event('descendants_reaped', descendants=statuses)
        return next((s['status'] for s in statuses if s['pid'] == pid), None)

    def guardian(self):
        if os.getsid(0) != os.getpid():
            os.setsid()
        prctl(36, 1)  # PR_SET_CHILD_SUBREAPER, before fork.
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: setattr(self, 'stop', True))
        self.prepare()
        self.phase('STARTING')
        read_fd, write_fd = os.pipe()
        guardian = os.getpid()
        fork_at = time.monotonic()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            try:
                self.controller(guardian, write_fd)
            except BaseException:
                os._exit(1)
        os.close(write_fd)
        self.status.update(controller_pid=pid, controller_start=stamp(pid))
        last = time.monotonic()
        startup_deadline = fork_at+3
        cleanup_at = None
        pending = b''
        reason = 'controller_eof'
        try:
            while True:
                now = time.monotonic()
                deadline = min(last+HEARTBEAT_TIMEOUT, cleanup_at or startup_deadline)
                if self.stop:
                    reason = 'guardian_signal'
                    break
                if now >= deadline:
                    reason = ('cap_cleanup' if cleanup_at and now >= cleanup_at else
                              'startup_timeout' if not cleanup_at and now >= startup_deadline else
                              'heartbeat_expired')
                    break
                if not select.select([read_fd], [], [], min(.1, deadline-now))[0]:
                    continue
                data = os.read(read_fd, 4096)
                if not data:
                    break
                pending += data
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    if line.startswith(b'R '):
                        require(cleanup_at is None, 'Duplicate readiness')
                        self.ready_at = float(line[2:])
                        require(fork_at <= self.ready_at <= time.monotonic(), 'Invalid readiness timestamp')
                        cleanup_at = self.ready_at+self.args.cap_seconds-OFF_RESERVE
                        self.status.update(ready=True, ready_monotonic=self.ready_at,
                                           cap_monotonic=self.ready_at+self.args.cap_seconds,
                                           cleanup_monotonic=cleanup_at)
                    else:
                        require(line == b'.', 'Invalid heartbeat')
                    last = time.monotonic()
            self.event(reason, heartbeat_age=time.monotonic()-last)
        except BaseException as error:
            reason = 'guardian_watch_error'
            self.event(reason, error=type(error).__name__)
        finally:
            os.close(read_fd)
            if reason == 'controller_eof' and not self.preimage.exists():
                # EOF immediately precedes C's _exit. Observe its owned zombie
                # without reaping, retaining PID/group identity through killpg.
                grace = time.monotonic()+.05
                while time.monotonic() < grace:
                    observed = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if observed is not None:
                        break
                    time.sleep(.002)
            child_status = self.kill_and_reap(pid)
        clean = reason == 'controller_eof' and child_status == 0 and not self.preimage.exists()
        for attempt in range(2):
            try:
                if clean:
                    require(all(self.control(n)[0] == 0 for n in AMPS), 'Final gates mismatch')
                    require(self.control(CLASS)[0] == self.saved['class'] and
                            self.control(GAIN)[0] == self.saved['gain'], 'Final preimage mismatch')
                else:
                    self.off(reason)
                    self.restore(self.saved)
                break
            except BaseException as error:
                clean = False
                self.event('cleanup_error', attempt=attempt+1, error=type(error).__name__)
        else:
            self.phase('ERROR', outcome='cleanup_unverified', lock_retained=True)
            self.event('cleanup_unverified_lock_retained')
            while True:
                signal.pause()
        self.event('cleanup_verified', reason=reason, normal=clean,
                   pcm_open=PCM.read_text().strip() != 'closed')
        self.phase('DONE', outcome=reason)
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode-dir', type=Path, required=True)
    parser.add_argument('--route-root', type=Path, default=Path('/run/asus-goodix-audio'))
    parser.add_argument('--cap-seconds', type=float, default=6)
    args = parser.parse_args()
    require(3.5 <= args.cap_seconds <= 6, 'Cap must be between 3.5 and 6 seconds')
    identity()
    private_dir(args.episode_dir)
    private_dir(args.route_root)
    require(args.route_root == Path('/run/asus-goodix-audio'), 'Use the shared owned-audio route root')
    require(not any(args.episode_dir.iterdir()), 'Episode directory must be fresh')
    os.umask(0o077)
    episode = Episode(args)
    try:
        return episode.guardian()
    except BaseException as error:
        episode.event('guardian_error', error=type(error).__name__)
        episode.phase('ERROR', error=type(error).__name__)
        if episode.locked:
            for attempt in range(2):
                try:
                    if any(episode.control(n)[0] != 0 for n in AMPS):
                        episode.off('startup_error')
                    break
                except BaseException as cleanup_error:
                    episode.event('cleanup_error', attempt=attempt+1, error=type(cleanup_error).__name__)
            else:
                episode.phase('ERROR', outcome='cleanup_unverified', lock_retained=True)
                episode.event('cleanup_unverified_lock_retained')
                while True:
                    signal.pause()
        return 1
    finally:
        # Never explicitly LOCK_UN: this description is shared with C/writers.
        # On failures, retain preimage; inheriting writers retain kernel exclusion.
        if episode.lock is not None:
            os.close(episode.lock)
        os.close(episode.events)


if __name__ == '__main__':
    sys.exit(main())
