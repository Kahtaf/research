"""Load byte-exact immutable rescue modules after verifying their original pins."""
import hashlib
import importlib.util
import sys
from pathlib import Path

PINS = {
    'manifest': 'c9a40f5e1029e8252abc9a8256d63d9fae0d4e1c5373eb247dc76e2e06c52ae2',
    'client': '0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69',
}

def load(name):
    path = Path(__file__).parent / 'original' / (name + '.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != PINS[name]:
        raise ValueError('original source pin mismatch: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

manifest = load('manifest')
client = load('client')
