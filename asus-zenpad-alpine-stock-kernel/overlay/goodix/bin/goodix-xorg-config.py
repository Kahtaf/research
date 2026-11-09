#!/usr/bin/env python3
"""Fill the native Goodix template, optionally selecting startup landscape."""
from pathlib import Path
import argparse, re, sys


def render(template, device, rotation=None):
    if not re.fullmatch(r'/dev/input/event(?:0|[1-9][0-9]*)', device):
        raise ValueError('Expected the validated canonical input event path')
    touch = '    Option "Device" "@GOODIX_DEVICE@"'
    framebuffer = '    Option "fbdev" "/dev/fb0"'
    if template.count(touch) != 1 or template.count(framebuffer) != 1:
        raise ValueError('Unexpected native Xorg template')
    if rotation not in (None, 'cw-v1'):
        raise ValueError('Only the reviewed CW landscape trial is supported')
    template = template.replace(touch, touch.replace('@GOODIX_DEVICE@', device))
    if rotation == 'cw-v1':
        if '    DefaultFbBpp 32\n' not in template:
            raise ValueError('Rotation requires the qualified 32-bit framebuffer')
        template = template.replace(framebuffer, framebuffer+'\n    Option "Rotate" "CW"')
        template = template.replace(touch.replace('@GOODIX_DEVICE@', device),
            touch.replace('@GOODIX_DEVICE@', device)+'\n    Option "CalibrationMatrix" "0 1 0 -1 0 1 0 0 1"')
    return template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('--device', required=True)
    parser.add_argument('--rotation-file', type=Path)
    args = parser.parse_args()
    rotation = None
    if args.rotation_file is not None:
        marker = args.rotation_file.read_text()
        if marker != 'cw-v1\n':
            raise ValueError('Unrecognized rotation marker')
        rotation = marker.strip()
    sys.stdout.write(render(args.template.read_text(), args.device, rotation))


if __name__ == '__main__':
    main()
