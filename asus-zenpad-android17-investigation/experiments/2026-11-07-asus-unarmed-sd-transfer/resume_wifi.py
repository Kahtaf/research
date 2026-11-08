"""Finish only the reconciled missing source files, using authenticated Wi-Fi ADB."""
from pathlib import Path
import datetime
import fcntl
import importlib.util
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('unarmed_transfer_boundary', ROOT / 'transfer.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.SERIAL = 'IP_REDACTED:5555'
state = dict(status='PREPARING_RECONCILED_COPY', endpoint=base.SERIAL,
             internal_partition_writes=False, execution_controls_copied=False)


def save():
    path = ROOT / 'evidence/wifi-resume.json'
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def main():
    os.umask(0o077)
    prior = json.loads((ROOT / 'evidence/transfer.json').read_text())
    inventory = json.loads((ROOT / 'evidence/wifi-reconciliation-inventory.json').read_text())
    assert prior['status'] == 'UNKNOWN_OR_INCOMPLETE_NO_RETRY'
    assert prior['copies'][0]['status'] == 'COPY_COMPLETED'
    assert inventory['same_boot_verified'] and len(inventory['resend_files']) == 252
    assert inventory['resend_bytes'] == 264241152
    with (ROOT / 'evidence/wifi-resume-started.json').open('x') as stream:
        json.dump(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    with (base.WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        base.shell('[ ! -e ' + base.CARD + '/asus-rescue.mode ]\n'
                   '[ ! -e ' + base.CARD + '/asus-rescue/execute.trigger ]\n')
        stage = ROOT / 'private/wifi-resume'
        stage.mkdir(parents=True)
        for relative in inventory['resend_files']:
            parts = Path(relative).parts
            assert len(parts) == 3 and parts[:2] == ('asus-rescue', 'role-2')
            assert len(parts[2]) == 10 and parts[2][:6].isdigit() and parts[2].endswith('.raw')
            source = base.SOURCE / relative
            assert source.is_file() and not source.is_symlink()
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, destination)
        state.update(status='COPYING_RECONCILED_MISSING_FILES', files=252, bytes=264241152,
                     started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save()
        with (ROOT / 'evidence/wifi-resume.log').open('xb') as log:
            result = subprocess.run([base.ADB, '-s', base.SERIAL, 'push',
                                     str(stage / 'asus-rescue'), base.CARD + '/'],
                                    env=base.ENV, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        state['adb_exit'] = result.returncode
        if result.returncode:
            raise RuntimeError('Wi-Fi source copy incomplete; no retry')
        rows = base.shell('sync\n[ ! -e ' + base.CARD + '/asus-rescue.mode ]\n'
                          '[ ! -e ' + base.CARD + '/asus-rescue/execute.trigger ]\n'
                          '[ ! -e ' + base.CARD + '/asus-stock/system.trigger ]\n'
                          '[ ! -e ' + base.CARD + '/asus-stock/boot.trigger ]\n'
                          '[ ! -e ' + base.CARD + '/asus-stock-report ]\n'
                          '[ ! -e ' + base.CARD + '/asus-rescue-report ]\n'
                          'mkdir ' + base.CARD + '/asus-stock-report ' + base.CARD + '/asus-rescue-report\n'
                          'find ' + base.CARD + '/asus-stock ' + base.CARD + '/asus-rescue -type f | wc -l\n')
        if rows != ['5409']:
            raise RuntimeError('Final source count mismatch')
        state.update(status='UNARMED_SOURCE_COPY_COMPLETE', total_files=5409,
                     total_source_bytes=5687439360, device_source_hashes_verified=False,
                     frontend_complete_hash_preflight_still_required=True,
                     ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save()
        print(json.dumps(state), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        state.update(status='UNKNOWN_OR_INCOMPLETE_NO_RETRY', error=type(error).__name__ + ': ' + str(error))
        save()
        raise
