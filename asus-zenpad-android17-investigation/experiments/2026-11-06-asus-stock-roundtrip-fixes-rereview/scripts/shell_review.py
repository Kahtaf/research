"""Real host POSIX shell; synthetic metadata nodes and power/mount files only."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[1]
P = R.parent / '2026-11-06-asus-stock-roundtrip-parent-fixes'
sys.dont_write_bytecode = True
sys.path.insert(0, str(P / 'source/service'))
import transport as T

def isolation(event, args):
    if event == 'subprocess.Popen':
        argv = args[1]
        if not (argv[0] == '/bin/sh' and argv[1] in ('-c', '-n')):
            raise RuntimeError('Only host synthetic shell checks allowed')
    elif event.startswith(('socket.', 'os.spawn', 'os.exec', 'os.posix_spawn')) or event == 'os.system':
        raise RuntimeError('Offline only')
sys.addaudithook(isolation)

records = []
for name, change, expected in [
    ('valid_full_metadata', {}, True),
    ('p12_wrong_major', {'p12_listing': 'brw------- 1 0 0 180, 12 2000-01-01 00:00 /dev/block/mmcblk0p12'}, False),
    ('p12_wrong_minor', {'p12_listing': 'brw------- 1 0 0 179, 13 2000-01-01 00:00 /dev/block/mmcblk0p12'}, False),
    ('p24_extra_field', {'p24_listing': 'brw------- 1 0 0 179, 24 2000-01-01 00:00 /dev/block/mmcblk0p24 EXTRA'}, False),
    ('p24_wrong_name', {'p24_listing': 'brw------- 1 0 0 179, 24 2000-01-01 00:00 /dev/block/mmcblk0p25'}, False),
    ('wrong_para_alias', {'para_alias': '/dev/block/mmcblk0p13'}, False),
    ('wrong_cache_alias', {'cache_alias': '/dev/block/mmcblk0p25'}, False),
    ('wrong_cache_geometry', {'cache_size': '409601'}, False),
    ('wrong_para_geometry', {'para_start': '225577'}, False),
    ('cache_is_symlink', {'symlink': 'cache'}, False),
    ('recovery_is_symlink', {'symlink': 'recovery'}, False),
    ('dangling_command_symlink', {'symlink': 'command'}, False),
    ('command_directory', {'command_dir': True}, False),
    ('tab_delimited_mount_not_accepted', {'mount': '/dev/block/mmcblk0p24\t/cache\text4\trw\t0\t0\n'}, False),
    ('missing_mount_fields', {'mount': '/dev/block/mmcblk0p24 /cache ext4 rw\n'}, False),
    ('mount_escaped_wrong_source', {'mount': '/dev/block/mmcblk0p24\\040bad /cache ext4 rw 0 0\n'}, False),
    ('usb_duplicate_without_final_newline', {'usb': 'POWER_SUPPLY_ONLINE=1\nPOWER_SUPPLY_ONLINE=1'}, False),
    ('battery_duplicate_without_final_newline', {'battery_suffix': 'POWER_SUPPLY_PRESENT=1'}, False),
    ('valid_no_final_newline', {'battery_no_newline': True}, True),
    ('voltage_whitespace', {'voltage': '4000 '}, False),
    ('voltage_command_substitution_literal', {'voltage': '$(false)'}, False),
]:
    with tempfile.TemporaryDirectory(dir=R / 'tests') as temporary:
        d = Path(temporary)
        cache = d / 'cache'
        cache.mkdir()
        recovery = cache / 'recovery'
        recovery.mkdir()
        if change.get('symlink') == 'cache':
            recovery.rmdir(); cache.rmdir(); cache.symlink_to(d / 'absent')
        elif change.get('symlink') == 'recovery':
            recovery.rmdir(); recovery.symlink_to(d / 'absent')
        elif change.get('symlink') == 'command':
            (recovery / 'command').symlink_to(d / 'absent')
        if change.get('command_dir'):
            (recovery / 'command').mkdir()
        battery = ('POWER_SUPPLY_BATT_VOL=' + change.get('voltage', '4000') + '\n'
                   'POWER_SUPPLY_PRESENT=1\nPOWER_SUPPLY_HEALTH=Good\n'
                   'POWER_SUPPLY_CAPACITY=80\nPOWER_SUPPLY_BATT_TEMP=250\n')
        battery += change.get('battery_suffix', '')
        if change.get('battery_no_newline'):
            battery = battery.rstrip('\n')
        (d / 'battery').write_text(battery)
        (d / 'usb').write_text(change.get('usb', 'POWER_SUPPLY_ONLINE=1\n'))
        (d / 'mounts').write_text(change.get('mount', '/dev/block/mmcblk0p24 /cache ext4 rw 0 0\n'))
        script = T.METADATA_GUARDS
        for part in ('12', '24'):
            script = script.replace('[ -b /dev/block/mmcblk0p' + part + ' ]',
                                    'asus_fixture_block /dev/block/mmcblk0p' + part)
        for old, new in [('/proc/mounts', str(d / 'mounts')),
                         ('/sys/class/power_supply/battery/uevent', str(d / 'battery')),
                         ('/sys/class/power_supply/usb/uevent', str(d / 'usb')),
                         ('/cache/recovery', str(recovery)),
                         ('[ ! -L /cache ]', '[ ! -L ' + str(cache) + ' ]'),
                         ('[ -d /cache ]', '[ -d ' + str(cache) + ' ]')]:
            script = script.replace(old, new)
        values = {
            '/sys/class/block/mmcblk0p12/partition': '12',
            '/sys/class/block/mmcblk0p12/start': change.get('para_start', '225576'),
            '/sys/class/block/mmcblk0p12/size': '1024',
            '/sys/class/block/mmcblk0p12/dev': '179:12',
            '/sys/class/block/mmcblk0p24/partition': '24',
            '/sys/class/block/mmcblk0p24/start': '662824',
            '/sys/class/block/mmcblk0p24/size': change.get('cache_size', '409600'),
            '/sys/class/block/mmcblk0p24/dev': '179:24',
        }
        prefix = '''set -eu
PATH=/nonexistent
asus_fixture_block() {
 case "$1" in /dev/block/mmcblk0p12|/dev/block/mmcblk0p24) return 0;; *) return 1;; esac
}
'''
        prefix += 'cat() { case "$1" in\n' + ''.join(
            shlex.quote(k) + ') printf "%s\\n" ' + shlex.quote(v) + ';;\n' for k, v in values.items())
        prefix += '*) return 99;; esac; }\n'
        prefix += 'ls() { case "$2" in\n'
        for part in ('12', '24'):
            listing = change.get('p' + part + '_listing', 'brw------- 1 0 0 179, ' + part + ' 2000-01-01 00:00 /dev/block/mmcblk0p' + part)
            prefix += '/dev/block/mmcblk0p' + part + ') printf "%s\\n" ' + shlex.quote(listing) + ';;\n'
        prefix += '*) return 99;; esac; }\n'
        prefix += 'readlink() { case "$2" in\n'
        for key, part in [('para', '12'), ('cache', '24')]:
            prefix += '*/by-name/' + key + ') printf "%s\\n" ' + shlex.quote(change.get(key + '_alias', '/dev/block/mmcblk0p' + part)) + ';;\n'
        prefix += '*) printf "%s\\n" "$2";; esac; }\n'
        result = subprocess.run(['/bin/sh', '-c', prefix + script], capture_output=True, text=True, timeout=3)
        records.append(dict(case=name, exit_status=result.returncode, expected_accept=expected,
                            passed=(result.returncode == 0) == expected, stderr=result.stderr))
syntax = subprocess.run(['/bin/sh', '-n', str(R / 'evidence/generated-write-helper-script.sh')],
                        capture_output=True, text=True, timeout=3)
receipt = dict(cases=records, generated_helper_syntax_exit=syntax.returncode,
               passed=all(x['passed'] for x in records) and syntax.returncode == 0,
               device_contacted=False,
               limits='Host /bin/sh only. Actual METADATA_GUARDS with synthetic path substitutions; node test, cat, ls, readlink outputs mocked with shell functions. No root script executed; captured helper script parsed with -n only.')
(R / 'evidence/shell-adversarial.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(vectors=len(records), passed=receipt['passed'], syntax_exit=syntax.returncode)))
raise SystemExit(not receipt['passed'])
