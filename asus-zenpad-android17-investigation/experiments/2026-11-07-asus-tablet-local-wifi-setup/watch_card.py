"""Bounded read-only wait for the owner's physical SD insertion. No root/reboot."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds', type=int, default=3600)
    args = p.parse_args()
    if not 5 <= args.seconds <= 21600 or args.seconds % 5:
        raise ValueError('Expected a bounded multiple of five seconds')
    env = {k:v for k,v in os.environ.items()
           if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
    env['PATH'] = str(ROOT.parent/'2026-11-07-asus-wifi-microsd-probe/source') + ':/opt/homebrew/bin:/usr/bin:/bin'
    start = datetime.datetime.now(datetime.timezone.utc)
    output = ROOT/'evidence'/('card-wait-'+start.strftime('%Y%m%dT%H%M%SZ')+'.json')
    script = ('i=0; while [ "$i" -lt ' + str(args.seconds//5) + ' ]; do '
              'if test -r /sys/class/block/mmcblk1p1/dev; then '
              'printf "CARD_PRESENT\\n"; cat /sys/class/block/mmcblk1p1/dev; '
              'cat /proc/sys/kernel/random/boot_id; exit 0; fi; '
              'i=$((i+1)); sleep 5; done; printf "CARD_ABSENT_AT_DEADLINE\\n"; exit 2')
    print(json.dumps(dict(state='READ_ONLY_CARD_WAIT_STARTED',seconds=args.seconds,receipt=str(output))),flush=True)
    try:
        result = subprocess.run(['adb','-s','IP_REDACTED:5555','shell',script],
                                env=env,capture_output=True,text=True,timeout=args.seconds+30)
        record = dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
    except subprocess.TimeoutExpired:
        record = dict(outcome='HOST_OBSERVATION_TIMEOUT',target_read_loop_bound_seconds=args.seconds)
    record.update(started_utc=start.isoformat(),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  device_writes=False,reboot=False)
    with output.open('x') as f:
        json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(record),flush=True)


if __name__ == '__main__':
    main()
