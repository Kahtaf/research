#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the physical Goodix panel and prepare its native libinput path."""
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def ioctl_bits(fd, number, size=8):
    data = bytearray(size)
    fcntl.ioctl(fd, 0x80004500 | (size << 16) | number, data)
    return int.from_bytes(data, sys.byteorder)


def root_directory(path):
    path.mkdir(mode=0o755, exist_ok=True)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0
            and not info.st_mode & 0o022, f'Unsafe directory: {path}')


def prepare_metadata(devnum):
    for path in [Path('/run'), Path('/run/udev'), Path('/run/udev/data')]:
        root_directory(path)
    filename = f'c{os.major(devnum)}:{os.minor(devnum)}'
    required = {'ID_INPUT': '1', 'ID_INPUT_TOUCHSCREEN': '1'}
    directory = os.open('/run/udev/data', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
        except FileNotFoundError:
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o644, dir_fd=directory)
            try:
                with os.fdopen(fd, 'w') as stream:
                    stream.write(''.join(f'E:{key}={value}\n'
                                         for key, value in required.items()))
            except BaseException:
                os.unlink(filename, dir_fd=directory)
                raise
            return f'/run/udev/data/{filename}'
        with os.fdopen(fd, 'r') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0
                    and not info.st_mode & 0o022, f'Unsafe metadata: {filename}')
            properties = {key: [] for key in required}
            for line in stream:
                if len(line) < 4:
                    break
                require(line.endswith('\n'), f'Unterminated metadata record: {filename}')
                key, separator, value = line.rstrip('\n').removeprefix('E:').partition('=')
                if line.startswith('E:') and separator and key in required:
                    properties[key].append(value)
            require(all(properties[key] and all(value == expected for value in properties[key])
                        for key, expected in required.items()),
                    f'Existing metadata has conflicting or missing input properties: {filename}')
        return f'/run/udev/data/{filename}'
    finally:
        os.close(directory)


def main():
    require(os.geteuid() == 0, 'Must run as root')
    require(len(sys.argv) == 2 and re.fullmatch(r'/dev/input/event[0-9]+', sys.argv[1]),
            'Usage: goodix-native-input.py /dev/input/eventN')
    panel = Path(sys.argv[1])
    panels = [entry for entry in Path('/sys/class/input').glob('event*')
              if (entry / 'device/name').read_text().strip() == 'goodix-touchscreen']
    require(len(panels) == 1, f'Expected one goodix-touchscreen; found {len(panels)}')
    entry = panels[0]
    require(panel.name == entry.name, f'Argument is not the discovered panel: {panel}')
    major, minor = map(int, (entry / 'dev').read_text().strip().split(':'))
    expected_devnum = os.makedev(major, minor)
    axes = {}
    fd = os.open(panel, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISCHR(info.st_mode) and info.st_rdev == expected_devnum,
                f'Panel character device does not match sysfs: {panel}')
        require(ioctl_bits(fd, 0x20) & (1 << 3), 'Panel lacks EV_ABS')
        require(ioctl_bits(fd, 0x09) & (1 << 1), 'Panel lacks INPUT_PROP_DIRECT')
        absolute_bits = ioctl_bits(fd, 0x23)
        for name, code in [('slot', 0x2f), ('x', 0x35), ('y', 0x36), ('tracking_id', 0x39)]:
            require(absolute_bits & (1 << code), f'Panel lacks MT {name} capability')
            raw = bytearray(24)
            fcntl.ioctl(fd, 0x80184540 + code, raw)
            value, minimum, maximum, fuzz, flat, resolution = struct.unpack('=6i', raw)
            require(maximum > minimum, f'Invalid MT {name} range: {minimum}..{maximum}')
            axes[name] = {'minimum': minimum, 'maximum': maximum}
        require(axes['slot']['minimum'] == 0, 'Panel MT slots do not begin at zero')
        result = subprocess.run(['udevadm', 'test-builtin', 'input_id', str(entry)],
                                capture_output=True, text=True, timeout=10, check=True)
        classification = (result.stdout + '\n' + result.stderr).splitlines()
        require('ID_INPUT=1' in classification and 'ID_INPUT_TOUCHSCREEN=1' in classification,
                'udevadm input_id did not classify the panel as a touchscreen')
        require(panel.lstat().st_rdev == expected_devnum,
                'Panel device changed during validation')
        metadata = prepare_metadata(expected_devnum)
        root_directory(Path('/dev/input'))
        print(json.dumps({'device': str(panel), 'devnum': f'{major}:{minor}',
                          'axes': axes, 'metadata': metadata}), file=sys.stderr)
        # xf86-input-libinput's open_restricted callback compares this literally
        # with udev's canonical devnode; a Device symlink is not accepted.
        print(panel)
    finally:
        os.close(fd)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f'goodix-native-input: {error}')
