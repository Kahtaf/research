#!/usr/bin/env python3
"""Continue the real ASUS userspace build after its current build exits."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path('/srv/android/asus-device-product')
TREE = Path('/srv/android/lineage24')
LOG = ROOT / 'logs/legacy-userspace-build.log'
STATE = ROOT / 'logs/legacy-userspace-job.json'


def save(status, **extra):
    data = dict(status=status, updated=datetime.datetime.now(datetime.timezone.utc).isoformat(), **extra)
    STATE.write_text(json.dumps(data, indent=2) + '\n')


def process_token(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


def apply_series():
    root = ROOT / 'compatibility'
    series = json.loads((root / 'series.json').read_text())
    assert not (root / 'applied.json').exists(), 'Already applied; inspect the saved checkpoint before rerunning'
    before = {}
    # Check the complete sequence on copies before changing any platform source.
    with tempfile.TemporaryDirectory(prefix='asus-compat-') as temporary:
        staging = Path(temporary)
        for item in series['patches']:
            patch = root / item['patch']
            assert hashlib.sha256(patch.read_bytes()).hexdigest() == item['sha256']
            project = item['project']
            for line in patch.read_text().splitlines():
                if not line.startswith('+++ b/'):
                    continue
                relative = Path(project) / line[6:]
                destination = staging / relative
                if destination.exists():
                    continue
                original = TREE / relative
                before[str(relative)] = hashlib.sha256(original.read_bytes()).hexdigest()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(original.read_bytes())
            subprocess.run(['git', 'apply', str(patch)], cwd=staging / project, check=True)
        active = subprocess.run(['pgrep', '-af', r'out/soong_ui --build-mode|prebuilts/siso/linux-x86/siso'], capture_output=True, text=True)
        assert not active.stdout.strip(), 'Another platform build is active: ' + active.stdout
        for relative, digest in before.items():
            assert hashlib.sha256((TREE / relative).read_bytes()).hexdigest() == digest
        for item in series['patches']:
            subprocess.run(['git', 'apply', str(root / item['patch'])], cwd=TREE / item['project'], check=True)
        projects = {}
        for project in sorted({item['project'] for item in series['patches']}):
            head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=TREE / project, text=True).strip()
            diff = subprocess.check_output(['git', 'diff', '--binary'], cwd=TREE / project)
            output = root / (project.replace('/', '-') + '-applied.diff')
            output.write_bytes(diff)
            projects[project] = dict(head=head, diff_sha256=hashlib.sha256(diff).hexdigest())
        (root / 'applied.json').write_text(json.dumps(dict(before=before, projects=projects, series=series), indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--after-pid', type=int, required=True)
    args = parser.parse_args()
    token = process_token(args.after_pid)
    marker = ROOT / 'logs/framework-build-complete'
    save('waiting_for_framework', framework_pid=args.after_pid, process_start_ticks=token)
    deadline = time.monotonic() + 4 * 3600
    while token and process_token(args.after_pid) == token:
        if time.monotonic() > deadline:
            raise RuntimeError('Framework wait deadline reached; source left unchanged')
        time.sleep(15)
    assert marker.exists(), 'Framework build did not complete; source left unchanged'
    framework_log = (ROOT / 'logs/framework-build.log').read_text(errors='replace')
    assert 'build completed successfully' in framework_log, 'Missing framework success result'
    save('applying_legacy_compatibility')
    apply_series()
    shutil.copytree(ROOT / 'staged-hardware/p00a-lights', TREE / 'device/asus/p00a/lights')
    save('building', build_script=str(ROOT / 'build_legacy_userspace.sh'))
    with LOG.open('w') as stream:
        result = subprocess.run(['timeout', '14400', 'bash', str(ROOT / 'build_legacy_userspace.sh')], stdout=stream, stderr=subprocess.STDOUT)
    assert result.returncode == 0, f'Userspace build exited {result.returncode}; see {LOG}'
    (ROOT / 'logs/legacy-userspace-build-complete').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
    save('completed', build_log=str(LOG))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('failed', error=str(error), build_log=str(LOG))
        raise
