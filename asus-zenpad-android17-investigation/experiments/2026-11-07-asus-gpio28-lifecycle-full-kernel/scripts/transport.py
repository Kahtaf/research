from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run
L = Path(__file__).resolve().parents[1]
R = '/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1'
