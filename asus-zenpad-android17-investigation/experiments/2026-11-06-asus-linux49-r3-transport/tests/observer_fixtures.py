"""Pure in-memory fixtures extracted from the pinned observer tests."""
import subprocess
from types import ModuleType
# Injected by test_transport; no device implementation is constructed here.
o: ModuleType
STOCK_ROW = dict(serial='DEVICE_SERIAL_REDACTED', state='device', usb='17895424X', product='WW_P00A',
                 model='P00A', device='P00A_2', transport_id='17')
PROBE_ROW = dict(serial='P00A49PROBE', state='recovery', usb='17895424X', product='p00a_diagnostic',
                 model='P00A_RAM_diagnostic', device='p00a', transport_id='18')

def report(changes: dict[str, str] | None = None) -> bytes:
    sections = {p: 'observed' for p in o.PATHS}
    sections.update({'/proc/version': 'Linux version 4.9.337 (builder@host) #1 SMP',
                     '/proc/cmdline': 'console=tty0 androidboot.serialno=' + o.STOCK + ' initrd=0x44000000,0x11f7b0',
                     '/proc/uptime': '24.03 19.91',
                     '/proc/mounts': 'rootfs / rootfs rw 0 0\nproc /proc proc rw 0 0\nadb /dev/usb-ffs/adb functionfs rw 0 0',
                     '/sys/fs/selinux/enforce': '1', '/proc/self/attr/current': 'u:r:recovery:s0\0',
                     '/sys/class/udc/musb-hdrc/state': 'configured', '/config/usb_gadget/g1/UDC': 'musb-hdrc'})
    sections.update({'entries ' + p: 'entry' for p in o.DIRS})
    sections[o.LABELS[-1]] = 'syslog result=-13'
    sections.update(changes or {})
    text = o.PREFIX + 'No block-device opens, mounts, module loads or peripheral control.\n'
    for label in o.LABELS:
        text += '\n[ ' + label + ' ]\n' + sections[label] + '\n'
    return (text + '\nEND_DIAGNOSTIC\n').encode()

class FakeAdb:
    def __init__(self, data: bytes, error: str | None = None) -> None:
        self.rows = iter([STOCK_ROW, PROBE_ROW, STOCK_ROW])
        self.data = data
        self.error = error

    def inventory(self) -> list[dict[str, str]]:
        return [next(self.rows)]

    def target(self, row: dict[str, str], command: list[str], pin: dict | None = None) -> subprocess.CompletedProcess[bytes]:
        if command == ['shell', 'report']:
            if self.error:
                raise o.Refused(self.error)
            return subprocess.CompletedProcess([], 0, self.data, b'')
        if command[-1] == 'getenforce':
            data = b'Enforcing\n'
        else:
            data = (o.PROPS[command[-1]] + '\n').encode()
        return subprocess.CompletedProcess([], 0, data, b'')
