"""Collect the complete retained log after the first Linux4.9 v2 checkpoint trial."""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import re
import secrets
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
HELPER = WORK / '2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py'
HELPER_SHA = '684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34'
SHIM = WORK / '2026-11-07-asus-wifi-microsd-probe/source'
SHIM_PINS = {'adb': '820fd0d66e75ee98701798e385f04e48a026ec7abd22ec6a67e9760ed0829e82',
             'legacy_adb.py': '6d00836d7e0cc28834f858b0fd6ab5515ffe7b3ecd37a6da6ba1f66b43597731'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boot-id', required=True)
    parser.add_argument('--trial-receipt', type=Path, required=True)
    args = parser.parse_args()
    if str(uuid.UUID(args.boot_id)) != args.boot_id:
        parser.error('Canonical observed stock boot UUID required')
    trial = json.loads(args.trial_receipt.read_text())
    if (trial.get('dispatch') not in ('ACKNOWLEDGED', 'UNKNOWN') or
            trial.get('previous_boot_id') == args.boot_id or
            not re.fullmatch('[0-9a-f]{64}', trial.get('candidate_p10_sha256', ''))):
        parser.error('Recorded candidate reboot dispatch and a different observed stock boot required')
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
        parser.error('Preserved stock helper changed')
    for name, expected in SHIM_PINS.items():
        if hashlib.sha256((SHIM / name).read_bytes()).hexdigest() != expected:
            parser.error('Preserved legacy ADB boundary changed')
    os.umask(0o077)
    run = str(uuid.uuid4())
    private = ROOT / 'artifacts/private/retained-trace' / run
    private.mkdir(parents=True, mode=0o700)
    public = ROOT / 'evidence' / ('retained-trace-' + run + '.json')
    token = secrets.token_hex(16)
    begin, end = 'ASUS_TRACE_' + token + '_BEGIN', 'ASUS_TRACE_' + token + '_END'
    script = ('[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + args.boot_id + ' ]\n'
              '[ -f /proc/last_kmsg ]\n[ ! -L /proc/last_kmsg ]\n'
              'printf "\\n' + begin + '\\n"\n'
              'dd if=/proc/last_kmsg bs=4096 count=513 2>/dev/null\n'
              '[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + args.boot_id + ' ]\n'
              'printf "\\n' + end + '\\n"\n')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    env['PATH'] = str(SHIM) + os.pathsep + '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools' + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    state = dict(outcome='UNKNOWN', at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 boot_id=args.boot_id, trial_receipt=str(args.trial_receipt.resolve()),
                 candidate_p10_sha256=trial['candidate_p10_sha256'], byte_limit=2097152,
                 trial_dispatch=trial['dispatch'],
                 trial_entry_acknowledged=trial['dispatch'] == 'ACKNOWLEDGED',
                 internal_image_writes=False, root_command_reads_only=True,
                 preserved_on_demand_helper_staging=True, raw_directory=str(private))
    with (WORK / '2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (private / 'intent.json').write_text(json.dumps(state, indent=2) + '\n')
        try:
            result = subprocess.run(['python3', '-B', str(HELPER)], input=script.encode(),
                                    capture_output=True, env=env, timeout=90)
            (private / 'helper.stdout').write_bytes(result.stdout)
            (private / 'helper.stderr').write_bytes(result.stderr)
            state['helper_exit'] = result.returncode
            normalized = result.stdout.replace(b'\r\n', b'\n')
            first, last = ('\n' + begin + '\n').encode(), ('\n' + end + '\n').encode()
            if result.returncode or normalized.count(first) != 1 or normalized.count(last) != 1:
                raise RuntimeError('Helper completion or fresh read delimiters unverified; no retry')
            data = normalized.split(first, 1)[1].split(last, 1)[0]
            if len(data) > 2097152:
                raise RuntimeError('Read exceeded its fixed limit')
            (private / 'last_kmsg.txt').write_bytes(data)
            lines = data.decode('utf-8', errors='replace').splitlines()
            markers = [
                'ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init',
                'ASUS-e9-retained-v2 01 paging_init returned; trace ready',
            ]
            observed = [marker for marker in markers if any(marker in line for line in lines)]
            before_paging = markers[0] in observed
            after_paging = markers[1] in observed
            later = ['02 setup_arch returned', '03 before init_IRQ',
                     '04 init_IRQ returned', '05 before time_init', '06 time_init returned']
            if after_paging:
                position = next(i for i, line in enumerate(lines) if markers[1] in line)
                observed += [item for item in later if item in lines[position + 1:]]
            positive = before_paging or after_paging
            state.update(outcome='linux49_v2_checkpoint_observed' if positive else 'complete_log_collected_no_v2_checkpoint',
                         bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                         trace_positive=positive, checkpoints=observed,
                         before_paging_checkpoint=before_paging,
                         after_paging_checkpoint=after_paging,
                         missing_marker_does_not_prove_nonexecution=True,
                         complete_read=True, read_count_bytes=513*4096,
                         marker_has_runtime_uuid=False,
                         exact_running_image_identity_proven_by_marker_alone=False)
        except BaseException as error:
            state.update(error=type(error).__name__ + ': ' + str(error))
        finally:
            state['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            with public.open('x') as stream:
                json.dump(state, stream, indent=2)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
    print(json.dumps(state), flush=True)
    return 2 if state['outcome'] == 'UNKNOWN' else 0


if __name__ == '__main__':
    raise SystemExit(main())
