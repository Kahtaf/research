"""Adapted recovery engine fake: models files and bounded dd, never executes commands."""
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
c = None


class FakeAdbRoot:
    """Models remote files/block bytes and observable dd attempts, not the engine."""
    def __init__(self, stock: bytes, action: str = 'install', fault: str | None = None) -> None:
        self.block = stock
        self.files: dict[str, bytes] = {}
        self.calls: list[list[str]] = []
        self.root_scripts: list[str] = []
        self.writes: list[dict[str, Any]] = []
        self.fault = fault
        self.action = action
        self.session = c.BASE + '/' + action
        self.props = dict([('ro.serialno', c.SERIAL), ('ro.product.device', 'P00A_2'),
                           ('ro.build.version.sdk', '24'), ('ro.build.fingerprint', c.FINGERPRINT),
                           ('sys.boot_completed', '1'), ('ro.adb.secure', '1')])
        self.serial = c.ENDPOINT
        self.sysfs = {
            '/sys/class/block/mmcblk0p10/partition': '10',
            '/sys/class/block/mmcblk0p10/start': '160184',
            '/sys/class/block/mmcblk0p10/size': '32696',
            '/sys/class/block/mmcblk0p10/dev': '179:10',
            '/sys/class/block/mmcblk0/queue/logical_block_size': '512',
        }
        self.alias = c.BLOCK
        self.selinux = 'Enforcing'
        self.lost_at = None
        self.candidate_written = False
        self.restore_written = False
        self.stage_exists = False

    def __call__(self, argv: list[str], *, input: str | None = None, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ['adb', '-s', c.ENDPOINT]:
            args = argv[3:]
            if args == ['get-serialno']:
                return subprocess.CompletedProcess(argv, 0, self.serial + '\n', '')
            if args[:2] == ['shell', 'getprop']:
                return subprocess.CompletedProcess(argv, 0, self.props[args[2]] + '\n', '')
            if args == ['shell', 'getenforce']:
                return subprocess.CompletedProcess(argv, 0, self.selinux + '\n', '')
            if args[0] == 'push':
                assert args[2] == self.session + '/inbox/input.bin'
                self.files[args[2]] = Path(args[1]).read_bytes()
                return subprocess.CompletedProcess(argv, 0, 'pushed\n', '')
            if args[0] == 'pull':
                assert args[1] == self.session + '/inbox/readback.bin'
                Path(args[2]).write_bytes(self.files[args[1]])
                return subprocess.CompletedProcess(argv, 0, 'pulled\n', '')
            raise AssertionError('Unexpected ADB call: ' + repr(args))
        assert argv == [sys.executable, str(c.HELPER)], argv
        self.root_scripts.append(input)
        assert c.DEVICE_GUARD in input, 'Root guard missing'
        token = re.search(r'ASUS_RECOVERY_RC_([0-9a-f]{32})=', input).group(1)
        status, helper_status = 0, 0
        comparisons = re.findall(r'\[ "\$\(cat (/sys/class/[^ )]+)\)" = ([^ ]+) \]', input)
        assert len(comparisons) == 5
        geometry_ok = all(self.sysfs[path] == value for path, value in comparisons)
        alias_expected = re.search(r'\[ "\$\(readlink -f ' + re.escape(c.ALIAS) + r'\)" = ([^ ]+) \]', input).group(1)
        if not geometry_ok or self.alias != alias_expected:
            status = 1
        elif 'mkdir ' + self.session + '\n' in input:
            status = 1 if self.stage_exists else 0
            self.stage_exists = True
        elif re.search(r'dd if=\S+ of=' + re.escape(c.BLOCK) + ' ', input):
            match = re.search(r'dd if=(\S+) of=(\S+) bs=(\d+) count=(\d+)\n', input)
            assert match is not None, 'Unbounded write'
            source, target, bs, count = match.groups()
            assert int(bs) * int(count) == c.SIZE
            assert target == c.BLOCK
            kind = Path(source).stem
            assert kind in ('candidate', 'stock')
            payload = self.files[source]
            self.writes.append(dict(source=kind, target=target, bytes=len(payload), sha256=c.sha(payload)))
            if kind == 'candidate':
                self.candidate_written = True
                if self.fault == 'denied':
                    status = 13
                elif self.fault in ('partial', 'lost_write', 'inverse_failure', 'unhealthy_after_failure'):
                    self.block = payload[:c.SIZE // 2] + self.block[c.SIZE // 2:]
                    status = 5
                    if self.fault == 'unhealthy_after_failure':
                        self.props['sys.boot_completed'] = '0'
                    if self.fault == 'lost_write':
                        self.lost_at = len(self.calls)
                        raise subprocess.TimeoutExpired(argv, 95)
                elif self.fault == 'mismatch':
                    self.block = payload[:-1] + bytes([payload[-1] ^ 1])
                else:
                    self.block = payload
            else:
                self.restore_written = True
                if self.fault in ('inverse_failure', 'restore_failure'):
                    self.block = payload[:1024] + self.block[1024:]
                    status = 9
                elif self.fault == 'restore_mismatch':
                    self.block = payload[:-1] + bytes([payload[-1] ^ 1])
                else:
                    self.block = payload
        elif f'dd if={c.BLOCK} ' in input:
            if self.candidate_written and self.fault == 'lost_readback':
                self.lost_at = len(self.calls)
                raise subprocess.TimeoutExpired(argv, 95)
            if self.candidate_written and not self.restore_written and self.fault == 'read_error':
                status = 6
            else:
                self.files[self.session + '/inbox/readback.bin'] = self.block
        elif 'cp ' + self.session + '/inbox/input.bin ' in input:
            dest = re.search(r'cp \S+/inbox/input.bin (\S+)', input).group(1)
            self.files[dest] = self.files[self.session + '/inbox/input.bin']
            self.files[self.session + '/inbox/readback.bin'] = self.files[dest]
            if self.fault == 'staging_corruption':
                self.files[self.session + '/inbox/readback.bin'] = bytes(c.SIZE)
        elif 'rmdir ' + self.session + '\n' in input:
            if self.fault == 'cleanup':
                status = 7
            self.stage_exists = False
        else:
            raise AssertionError('Unexpected root script')
        stdout = f'root wrapper noise\nASUS_RECOVERY_RC_{token}={status}\n'
        if self.fault == 'helper_failed' and self.candidate_written:
            helper_status = 1
        if self.fault == 'missing_status' and self.candidate_written:
            stdout = 'lost completion record\n'
        return subprocess.CompletedProcess(argv, helper_status, stdout, '')


