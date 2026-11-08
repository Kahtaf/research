#!/usr/bin/env python3
"""Read-only remote source queries; program supplied on stdin."""
import pathlib, subprocess, sys
scope={"__file__": __file__}
exec((pathlib.Path(__file__).parent/'source_read.py').read_text().split('paths = sys.argv[1:]')[0],scope)
subprocess.run(scope['SSH']+['python3 -B -'],input=sys.stdin.buffer.read(),check=True)
