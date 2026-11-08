"""Owned bounded read-only SSH helper; no remote files are created."""
import importlib.util, subprocess, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('baseline_remote',Path('2026-11-06-asus-r8-continuation-kit/scripts/remote.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
script='import resource\nresource.setrlimit(resource.RLIMIT_CPU,(45,45))\nresource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))\n'+sys.stdin.read()
p=subprocess.run(m.SSH+['timeout 55s taskset -c 0 python3 -B -'],input=script,text=True,capture_output=True,timeout=60)
sys.stdout.write(p.stdout);sys.stderr.write(p.stderr)
raise SystemExit(p.returncode)
