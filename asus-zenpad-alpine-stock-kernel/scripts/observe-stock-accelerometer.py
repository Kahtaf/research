#!/usr/bin/env python3
"""Three-second passive evdev observation; never enable or configure sensors."""
from pathlib import Path
import fcntl
import json
import os
import select
import stat
import struct
import time

assert os.uname().release == '3.18.35' and os.uname().machine == 'aarch64'
assert Path('/etc/asus-alpine-ram-release').read_text().strip() == 'asus-alpine-stock-kernel-v1'
assert Path('/sys/bus/i2c/devices/2-0011/driver').resolve().name == 'BMA255'
events = [p for p in Path('/sys/class/input').glob('event*')
          if (p/'device/name').read_text().strip() == 'm_acc_input']
assert len(events) == 1
event = events[0]
major, minor = map(int, (event/'dev').read_text().split(':'))
node = Path('/dev/input')/event.name
record = struct.Struct('@llHHi')
assert record.size == 24
fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
cached = {}
frames = []
count = 0
try:
    info = os.fstat(fd)
    assert stat.S_ISCHR(info.st_mode) and info.st_rdev == os.makedev(major, minor)
    for axis in (0, 1, 2):
        buffer = bytearray(24)
        fcntl.ioctl(fd, 0x80184540+axis, buffer, True)  # EVIOCGABS, cached input state only.
        cached[axis] = struct.unpack('=6i', buffer)[0]
    baseline = dict(cached)
    pending = bytearray()
    relative = {}
    deadline = time.monotonic()+3
    started = time.monotonic()
    while time.monotonic() < deadline and count < 512 and len(frames) < 5:
        if not select.select([fd], [], [], max(0, deadline-time.monotonic()))[0]:
            break
        chunk = os.read(fd, record.size*64)
        assert chunk, 'Input device disappeared'
        pending.extend(chunk)
        while len(pending) >= record.size and count < 512 and len(frames) < 5:
            seconds, microseconds, kind, code, value = record.unpack(pending[:record.size])
            del pending[:record.size]
            count += 1
            if kind == 3 and code in (0, 1, 2):
                cached[code] = value
            elif kind == 2:
                relative[code] = value
            elif kind == 0 and code == 0:
                if all(c in relative for c in (0, 6, 7)):
                    frames.append({'cached_or_updated_axes':dict(cached), 'relative_update':relative[0],
                                   'timestamp_high':relative[6], 'timestamp_low':relative[7]})
                relative = {}
            elif kind == 0 and code == 3:
                raise RuntimeError('Evdev reader queue overflowed; no fresh-sample claim')
        if not pending and count >= 512:
            break
    elapsed = time.monotonic()-started
finally:
    os.close(fd)
print(json.dumps({'status':'FRESH_REPORTS_OBSERVED' if frames else 'NO_EXISTING_REPORTS_OBSERVED',
                  'seconds':elapsed, 'event_records':count, 'cached_axes_not_fresh':baseline,
                  'fresh_complete_frames':frames, 'sensor_driver_attributes_read':False, 'activation_writes':False,
                  'delay_writes':False, 'calibration_access':False, 'display_changed':False}))
