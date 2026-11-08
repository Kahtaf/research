"""Pinned P00A normal-BOOT metadata contract, not a hardware boot proof."""
import struct
from bootformat import ungzip
from fdt import parse

RAMDISK_START = 0x44000000
LK_DEFAULT = b'console=tty0 console=ttyMT3,921600n1 earlycon=uart8250,mmio32,0x11002000 root=/dev/ram vmalloc=496M androidboot.hardware=mt8163'
REQUIRED_INPUT = {
    b'bootopt': b'64S3,32N2,64N2', b'build_version': b'3',
    b'androidboot.hardware': b'mt8163', b'androidboot.fstab_suffix': b'mt8163',
    b'androidboot.boot_devices': b'soc/11230000.mmc',
}
OPTIONAL_INPUT = {b'androidboot.selinux': b'enforcing', b'enforcing': b'1'}
HEADER = b'bootopt=64S3,32N2,64N2 build_version=3 androidboot.boot_devices=soc/11230000.mmc enforcing=1'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def header_limit(cmd):
    need(isinstance(cmd, bytes) and 0 < len(cmd) <= 99, 'LK header must contain 1..99 bytes')
    need(all(32 <= b < 127 for b in cmd), 'Header must be printable ASCII without NUL')
    return cmd


def arguments(cmd):
    need(all(32 <= b < 127 for b in cmd), 'Arguments must be printable ASCII')
    result = {}
    for token in cmd.split():
        key, sep, value = token.partition(b'=')
        need(sep and key and value, 'Argument requires key=value')
        need(key not in result, 'Duplicate argument: ' + key.decode())
        result[key] = value
    return result


def narrow_header(cmd):
    args = arguments(cmd)
    need(set(args) <= REQUIRED_INPUT.keys() | OPTIONAL_INPUT.keys(), 'Unreviewed argument (including initrd)')
    for key, value in REQUIRED_INPUT.items():
        need(args.get(key) == value, 'Required argument missing/conflicting: ' + key.decode())
    for key, value in OPTIONAL_INPUT.items():
        need(key not in args or args[key] == value, 'Unsafe argument: ' + key.decode())
    return header_limit(HEADER)


def kernel_config(raw):
    begin, end = raw.find(b'IKCFG_ST'), raw.find(b'IKCFG_ED')
    need(begin >= 0 and end > begin, 'Embedded IKCONFIG required')
    config, tail = ungzip(raw[begin + 8:end])
    need(not tail, 'Unexpected IKCONFIG trailer')
    lines = set(config.splitlines())
    for line in [b'CONFIG_BLK_DEV_INITRD=y', b'CONFIG_CMDLINE_FROM_BOOTLOADER=y',
                 b'# CONFIG_CMDLINE_FORCE is not set', b'# CONFIG_CMDLINE_EXTEND is not set',
                 b'CONFIG_SECURITY_SELINUX=y', b'CONFIG_SECURITY_SELINUX_BOOTPARAM=y',
                 b'CONFIG_SECURITY_SELINUX_BOOTPARAM_VALUE=1', b'CONFIG_SECURITY_SELINUX_DEVELOP=y',
                 b'# CONFIG_SECURITY_SELINUX_DISABLE is not set']:
        need(line in lines, 'Unreviewed compiled kernel config: ' + line.decode())
    return config


def chosen_dt(data, length, cmd):
    """Replace exactly three chosen properties, matching LK's 32-bit bounds."""
    need(0 < length <= 0x400000, 'Ramdisk exceeds pinned first fixed reservation')
    header_limit(cmd)
    need(not any(t.startswith(b'initrd=') for t in cmd.split()), 'Explicit initrd override forbidden')
    h, nodes, tokens = parse(data)
    need('/chosen' in nodes, 'Missing chosen')
    need(not any('asus,allow-battery-charging' in p for p in nodes.values()), 'Charging opt-in forbidden')
    need(not any(t.startswith(b'initrd=') for t in nodes['/chosen'].get('bootargs', b'').rstrip(b'\0').split()), 'Inherited initrd override forbidden')
    # DT firmware properties outrank cmdline in SDK37: this contract uses its cmdline fallback.
    for path, props in nodes.items():
        need(not path.startswith('/firmware/android/fstab'), 'Unreviewed Android DT fstab node')
        if path.startswith('/firmware/android'):
            need(not set(props) & {'hardware', 'fstab_suffix', 'boot_devices', 'fstab'}, 'Unreviewed Android DT override')
    changes = {'bootargs': LK_DEFAULT + b' ' + cmd + b'\0',
               'linux,initrd-start': struct.pack('>I', RAMDISK_START),
               'linux,initrd-end': struct.pack('>I', RAMDISK_START + length)}
    strings = bytearray(data[h[3]:h[3] + h[8]])
    def prop(name, value):
        encoded = name.encode() + b'\0'; off = strings.find(encoded)
        if off < 0:
            off = len(strings); strings.extend(encoded)
        return struct.pack('>III', 3, len(value), off) + value + bytes(-len(value) % 4)
    stream = bytearray(); seen = set()
    for kind, node, name, value, original in tokens:
        if node == '/chosen' and kind == 3 and name in changes:
            stream += prop(name, changes[name]); seen.add(name)
        elif node == '/chosen' and kind == 2:
            for name, value in changes.items():
                if name not in seen: stream += prop(name, value)
            stream += original
        else: stream += original
    header = list(h); header[1] = h[2] + len(stream) + len(strings)
    header[3] = h[2] + len(stream); header[8] = len(strings); header[9] = len(stream)
    result = struct.pack('>10I', *header) + data[40:h[2]] + stream + strings
    expected = {n: dict(p) for n, p in nodes.items()}; expected['/chosen'].update(changes)
    need(parse(result)[1] == expected and result[40:h[2]] == data[40:h[2]], 'DT preservation failure')
    return bytes(result)


def model_lk_gzip(staging, wrapped_kernel_length, stream_length, expected_raw):
    """Exact scanned-tail rounding + host raw zlib substitute for LK inflate."""
    import hashlib
    import zlib
    selected = staging.rfind(b'\xd0\x0d\xfe\xed', 1, wrapped_kernel_length + 4)
    need(selected == stream_length, 'LK would select a different last DT magic')
    copied_tail = (wrapped_kernel_length - selected + 3) & ~3
    input_length = wrapped_kernel_length - copied_tail
    data = staging[:input_length]
    need(len(data) >= 10 and data[:3] == b'\x1f\x8b\x08' and not data[3] & 0xe0, 'LK gzip header rejection')
    flags = data[3]; pos = 10
    if flags & 4:
        need(len(data) >= 12, 'Truncated extra length')
        pos = 12 + struct.unpack_from('<H', data, 10)[0]
    for flag in (8, 16):
        if flags & flag:
            pos = data.index(b'\0', pos) + 1
    if flags & 2: pos += 2
    need(pos < len(data), 'LK gzip header exceeds supplied input')
    obj = zlib.decompressobj(-15)
    raw = obj.decompress(data[pos:], 0x1c00000 + 1)
    need(obj.eof and len(raw) <= 0x1c00000 and raw == expected_raw, 'LK raw inflate semantic model mismatch')
    return {'method': 'host raw zlib substitute, not LK execution', 'selected_dt_offset': selected,
            'copied_dt_tail_bytes': copied_tail, 'supplied_gzip_bytes': input_length,
            'unused_trailer_bytes': len(obj.unused_data), 'output_bytes': len(raw),
            'output_sha256': hashlib.sha256(raw).hexdigest(), 'capacity': 0x1c00000}
