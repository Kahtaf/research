"""Bounded host USB identity observation; no device or media writes."""
from pathlib import Path
import json
import subprocess

SERIAL = 'P499342cbf13bf044d4b655'
PREFIX = 'ASUS-PID1:'
def inspect():
    q = subprocess.run(['system_profiler', 'SPUSBHostDataType', '-json'],
                       capture_output=True, text=True, timeout=15, check=True)
    data = json.loads(q.stdout)
    found = []
    def walk(value):
        if isinstance(value, dict):
            texts = [v for v in value.values() if isinstance(v, str)]
            if SERIAL in texts or any(v.startswith(PREFIX) for v in texts):
                found.append({k:v for k,v in value.items() if isinstance(v, (str,int,bool))})
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(data)
    return {'matching_devices':found, 'P49RAM_mounted':Path('/Volumes/P49RAM').exists()}, q.stdout
if __name__ == '__main__':
    print(json.dumps(inspect()[0]))
