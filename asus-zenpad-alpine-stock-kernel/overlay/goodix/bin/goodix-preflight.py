#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Discover this panel and prove its axis ABI before running the donor bridge."""
import fcntl
import json
from pathlib import Path
import stat
import struct
import sys

panels = []
for entry in Path('/sys/class/input').glob('event*'):
    name = entry / 'device/name'
    if name.is_file() and name.read_text().strip() == 'goodix-touchscreen':
        panels.append(Path('/dev/input') / entry.name)
if len(panels) != 1:
    raise SystemExit(f'Expected one goodix-touchscreen; found {len(panels)}')
panel = panels[0]
if not stat.S_ISCHR(panel.stat().st_mode):
    raise SystemExit(f'{panel} is not a character device')
with panel.open('rb', buffering=0) as stream:
    axes = {}
    for name, code in [('slot', 0x2f), ('x', 0x35), ('y', 0x36)]:
        raw = bytearray(24)
        fcntl.ioctl(stream.fileno(), 0x80184540 + code, raw)
        value, minimum, maximum, fuzz, flat, resolution = struct.unpack('=6i', raw)
        if maximum <= minimum:
            raise SystemExit(f'Invalid {name} axis range: {minimum}..{maximum}')
        axes[name] = {'minimum': minimum, 'maximum': maximum}
    if axes['slot']['minimum'] != 0 or axes['slot']['maximum'] > 15:
        raise SystemExit('Panel slots exceed the donor bridge capacity (0..15)')
print(json.dumps({'device': str(panel), 'axes': axes}), file=sys.stderr)
print(panel)
