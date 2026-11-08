#!/usr/bin/env python3
"""Upload immutable r5 tooling and inputs using the existing SSH connection."""
from pathlib import Path
import io
import subprocess
import tarfile
from graphics_remote import SSH
ROOT = Path(__file__).resolve().parents[1]
remote = '/srv/android/asus-device-product'
data = io.BytesIO()
with tarfile.open(fileobj=data, mode='w') as t:
    for name in ['build_graphics.sh','capture_graphics_revision.py','run_graphics_revision.py',
                 'deploy_graphics_profile.py','prepare_graphics_blobs.py','deploy_vendor_graphics.py']:
        t.add(ROOT/'scripts'/name,arcname='revisions/r5/'+name)
    for name in ['linkerconfig.patch','source-manifest.json']:
        t.add(ROOT/'compatibility/graphics-r5'/name,arcname='revisions/r5/'+name)
    t.add(ROOT/'device/asus/p00a/device.mk',arcname='revisions/r5/device.mk')
    t.add(ROOT/'staged-hardware/p00a-lights/Android.bp',arcname='revisions/r5/lights.Android.bp')
    t.add(ROOT/'artifacts/vendor-graphics-inputs-r5.tar.gz',arcname='vendor-graphics-inputs-r5.tar.gz')
subprocess.run(SSH + [f'test ! -e {remote}/revisions/r5 && tar -xf - -C {remote}'], input=data.getvalue(), check=True)
print(f'Uploaded {len(data.getvalue())} bytes; exit 0')
