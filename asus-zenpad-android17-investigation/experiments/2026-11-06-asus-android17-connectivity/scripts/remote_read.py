#!/usr/bin/env python3
"""Read selected source files from the existing builder; never writes remotely."""
import hashlib, json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
SSH = ['ssh', '-i', str(pathlib.Path.home()/'.ssh/asus_p00a_android17'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=compute.8549823276971553556', '-o', 'UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'), 'android@IP_REDACTED']
def run(code):
    return subprocess.run(SSH+['python3 -'], input=code, text=True, capture_output=True, check=True).stdout
if __name__ == '__main__':
    paths = sys.argv[1:]
    for p in paths:
        if not (p.startswith('/srv/android/lineage24/') or p.startswith('/srv/android/asus-android17/')) or '..' in p.split('/'):
            raise SystemExit('Only explicit source/build evidence paths are accepted')
    code = 'import pathlib,json,hashlib\npaths='+repr(paths)+'\nout={}\nfor p in paths:\n b=pathlib.Path(p).read_bytes(); out[p]={"sha256":hashlib.sha256(b).hexdigest(),"text":b.decode()}\nprint(json.dumps(out))'
    data = json.loads(run(code))
    manifest_path = ROOT/'evidence/remote-files.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for p, info in data.items():
        dest = ROOT/'sources'/p.removeprefix('/srv/android/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(info['text'])
        manifest[p] = {'sha256': info['sha256'], 'local': str(dest.relative_to(ROOT))}
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print('Captured', len(data), 'source/evidence files, read-only')
