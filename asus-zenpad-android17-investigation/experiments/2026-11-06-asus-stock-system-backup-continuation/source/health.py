"""Fixed read-only batched health queries. Only transport 255/timeouts retry."""
import secrets
import shlex
import subprocess
from policy import ENDPOINT, SERIAL, FINGERPRINT, Stop, require

ADB = ['adb', '-s', ENDPOINT]
PROPS = {'ro.serialno': SERIAL, 'ro.product.device': 'P00A_2', 'ro.build.version.sdk': '24',
         'ro.build.fingerprint': FINGERPRINT, 'ro.adb.secure': '1', 'sys.boot_completed': '1'}

def snapshot_script(nonce):
    commands = ['set -eu', "printf '%s\\n' " + shlex.quote('BEGIN_'+nonce)]
    for key in PROPS:
        commands += [f"v=$(getprop {key})", f"printf '%s=%s\\n' {shlex.quote(key)} \"$v\""]
    commands += ['v=$(getenforce)', "printf 'selinux=%s\\n' \"$v\"",
                 "printf '%s\\n' " + shlex.quote('END_'+nonce)]
    return '\n'.join(commands)

def parse_snapshot(text, nonce):
    lines = text.splitlines()
    expected = ['BEGIN_'+nonce] + [k+'='+v for k, v in PROPS.items()] + ['selinux=Enforcing', 'END_'+nonce]
    require(lines == expected, 'Identity/security/health snapshot mismatch or malformed nonce envelope')
    return dict(**PROPS, selinux='Enforcing')

def query(argv, record, runner=None):
    runner = runner or subprocess.run
    for attempt in range(1, 4):
        record('health_dispatch', argv=argv, attempt=attempt)
        try:
            result = runner(argv, text=True, capture_output=True, timeout=12)
        except subprocess.TimeoutExpired as exc:
            def text(value):
                return value.decode('utf-8', 'replace') if isinstance(value, bytes) else (value or '')
            stdout, stderr = text(exc.stdout), text(exc.stderr)
            record('health_returned', attempt=attempt, timeout=True, stdout=stdout, stderr=stderr)
            require(not stdout.strip(), 'Partial timed-out health response; inspect before retry')
            if attempt == 3:
                raise Stop('Read-only health timeout exhausted; no root dispatch')
            continue
        record('health_returned', attempt=attempt, status=result.returncode,
               stdout=result.stdout, stderr=result.stderr)
        if result.returncode == 255 and attempt < 3:
            require(not result.stdout.strip(), 'Nonempty failed health response; inspect before retry')
            continue
        require(result.returncode == 0, 'Read-only health query failed')
        return result.stdout
    raise Stop('Health query exhausted')

def healthy(record, runner=None):
    require(query(ADB+['get-serialno'], record, runner).strip() == ENDPOINT, 'ADB endpoint mismatch')
    nonce = secrets.token_hex(16)
    return parse_snapshot(query(ADB+['shell', '-T', snapshot_script(nonce)], record, runner), nonce)
