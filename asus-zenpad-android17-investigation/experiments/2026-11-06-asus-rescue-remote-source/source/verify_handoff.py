"""Offline integrity and syntax check. Never opens images or runs transports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    pins = json.loads((ROOT/'SOURCE_PINS.json').read_text())
    checked=[]
    for relative, expected in pins.items():
        path=ROOT/relative
        if path.resolve().is_relative_to(ROOT) is False:
            raise ValueError('pin outside spike')
        data=path.read_bytes()
        if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:
            raise ValueError('handoff changed: '+relative)
        if path.suffix=='.py':compile(data,str(path),'exec')
        checked.append(relative)
    original=ROOT.parent/'2026-11-06-asus-android17-target-rescue/source'
    upstream=json.loads((ROOT/'profiles/original-source-pins.json').read_text())
    for name,digest in upstream.items():
        if hashlib.sha256((original/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('original rescue source changed: '+name)
    print(json.dumps({'mode':'OFFLINE_INTEGRITY_ONLY','pinned_files':len(checked),
                      'original_rescue_files_unchanged':list(upstream),
                      'source_payloads_read':False,'target_used':False},indent=2))

if __name__=='__main__':main()
