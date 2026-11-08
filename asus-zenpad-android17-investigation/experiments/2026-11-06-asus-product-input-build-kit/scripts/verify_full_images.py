#!/usr/bin/env python3
"""Check real full-product outputs on the builder; never accesses a device."""
import hashlib
import json
from pathlib import Path
import shlex
import struct
import sys
import zipfile


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def variables(path):
    values = {}
    for line in path.read_text().splitlines():
        key, separator, value = line.partition('=')
        if separator:
            values[key] = ' '.join(shlex.split(value))
    expected = dict(TARGET_BUILD_VARIANT='userdebug', TARGET_DEVICE='p00a', TARGET_ARCH='arm64',
                    TARGET_KERNEL_SOURCE='kernel/asus/p00a-fd',
                    PLATFORM_SDK_VERSION='37', PLATFORM_VERSION_LAST_STABLE='17',
                    PRODUCT_SHIPPING_API_LEVEL='23',
                    BOARD_BOOTIMAGE_PARTITION_SIZE='16740352',
                    BOARD_SYSTEMIMAGE_PARTITION_SIZE='3753902080',
                    TARGET_COPY_OUT_VENDOR='system/vendor',
                    TARGET_COPY_OUT_PRODUCT='system/product',
                    TARGET_COPY_OUT_SYSTEM_EXT='system/system_ext',
                    PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG='false',
                    PRODUCT_ADB_KEYS='device/asus/p00a/prebuilt/debug-adb-public-key',
                    BOARD_VNDK_VERSION='', PRODUCT_PRODUCT_VNDK_VERSION='current',
                    SOONG_CONFIG_p00a_legacy_graphics='true', SOONG_CONFIG_libion_legacy_impl='true')
    for name in ('BOOT', 'SYSTEM', 'RAMDISK'):
        expected[f'PRODUCT_BUILD_{name}_IMAGE'] = 'true'
    for name in ('INIT_BOOT', 'RECOVERY', 'VENDOR', 'PRODUCT', 'SYSTEM_EXT', 'USERDATA', 'VBMETA'):
        expected[f'PRODUCT_BUILD_{name}_IMAGE'] = 'false'
    for name, value in expected.items():
        if values.get(name) != value:
            raise ValueError(f'{name}: expected {value!r}, got {values.get(name)!r}')
    if values.get('SELINUX_IGNORE_NEVERALLOWS', '') not in ('', 'false'):
        raise ValueError('SELinux neverallow checks must remain enabled')
    if not values.get('PRODUCT_OUT'):
        raise ValueError('Missing PRODUCT_OUT')
    properties = ' '.join(values.get(name, '') for name in
                          ('PRODUCT_SYSTEM_PROPERTIES', 'PRODUCT_SYSTEM_EXT_PROPERTIES', 'PRODUCT_VENDOR_PROPERTIES')).split()
    # SDK37 keeps a vestigial product-variant default of 'current'. It does
    # not emit a VNDK runtime property; check that actual namespace input.
    if any(p.startswith(('ro.vndk.version=', 'ro.product.vndk.version=')) for p in properties):
        raise ValueError('Legacy graphics requires absent runtime VNDK properties')
    adb_security = [p.partition('=')[2] for p in properties if p.startswith('ro.adb.secure=')]
    if not adb_security or any(value != '1' for value in adb_security):
        raise ValueError('Effective product does not preserve authenticated ADB')
    required_packages = {'adb_root', 'com.android.adbd', 'android.hardware.keymaster@4.0-service', 'keystore2',
                         'Phonesky', 'GoogleServicesFramework', 'com.google.android.gmssystem.prodvic', 'p00a-wmt', 'libbtcal', 'libbt-vendor-p00a', 'libbluetooth_mtk_p00a', 'android.hardware.bluetooth@1.1-service.p00a', 'wpa_supplicant', 'P00aWifiBringupOverlay'}
    missing = required_packages - set(values.get('PRODUCT_PACKAGES', '').split())
    if missing:
        raise ValueError('Full product is missing required service/Google modules: ' + ', '.join(sorted(missing)))
    for required in ('androidboot.hardware=mt8163', 'androidboot.fstab_suffix=mt8163'):
        if required not in values.get('BOARD_KERNEL_CMDLINE', '').split():
            raise ValueError('Missing boot/fstab selector: ' + required)
    return values


def inspect_boot(path, limit, expected):
    data = path.read_bytes()
    if data[:8] != b'ANDROID!' or len(data) < 2048:
        raise ValueError('Expected an Android v0 boot image')
    ksize, kaddr, rsize, raddr, ssize, saddr, tags, page = struct.unpack_from('<8I', data, 8)
    version = struct.unpack_from('<I', data, 40)[0]
    if (page, version, ssize) != (2048, 0, 0):
        raise ValueError(f'Unexpected boot page/version/second size: {page}/{version}/{ssize}')
    if (kaddr, raddr, tags) != (0x40080000, 0x44000000, 0x4e000000):
        raise ValueError('Boot load addresses differ from the measured stock layout')
    align = lambda size: (size + page - 1) // page * page
    roffset = page + align(ksize)
    if not ksize or not rsize or roffset + rsize > len(data) or len(data) > limit:
        raise ValueError('Invalid boot component bounds or partition overflow')
    kernel = data[page:page + ksize]
    ramdisk = data[roffset:roffset + rsize]
    boot_id = hashlib.sha1(kernel + struct.pack('<I', ksize) + ramdisk +
                           struct.pack('<I', rsize) + struct.pack('<I', 0)).digest() + bytes(12)
    if data[576:608] != boot_id:
        raise ValueError('Boot header component digest is invalid')
    wrapped_kernel = kernel[:4] == bytes.fromhex('88168858')
    wrapped_ramdisk = ramdisk[:4] == bytes.fromhex('88168858')
    # Current AOSP mkbootimg writes zero when there is no second payload.
    # The final MTK repacker must preserve stock's otherwise unused address.
    if saddr not in (0, 0x40f00000) or (wrapped_kernel and wrapped_ramdisk and saddr != 0x40f00000):
        raise ValueError('Unexpected empty-second address for this packaging stage')
    if wrapped_kernel:
        if struct.unpack_from('<I', kernel, 4)[0] != len(kernel) - 512:
            raise ValueError('Incorrect MTK kernel payload length')
        kernel = kernel[512:]
    if hashlib.sha256(kernel).hexdigest() != expected:
        raise ValueError('Boot image does not contain the reviewed ASUS kernel')
    return dict(bytes=len(data), sha256=sha256(path), page_bytes=page,
                kernel_bytes=ksize, ramdisk_bytes=rsize,
                mtk_kernel_wrapper_present=wrapped_kernel,
                mtk_ramdisk_wrapper_present=wrapped_ramdisk,
                boot_header_digest_valid=True,
                empty_second_address=hex(saddr),
                packaging_review_required=True, hardware_boot_verified=False)


def inspect_system(path, limit):
    with path.open('rb') as stream:
        header = stream.read(28)
        if len(header) < 28:
            raise ValueError('Truncated system image')
        magic = struct.unpack_from('<I', header)[0]
        if magic == 0xed26ff3a:
            _, major, minor, file_header, chunk_header, block, blocks, chunks, checksum = struct.unpack('<I4H4I', header)
            if major != 1 or file_header < 28 or chunk_header < 12 or not block:
                raise ValueError('Unsupported sparse image layout')
            expanded = block * blocks
            stream.seek(file_header)
            counted = 0
            for _ in range(chunks):
                chunk = stream.read(chunk_header)
                if len(chunk) != chunk_header:
                    raise ValueError('Truncated sparse chunk header')
                kind, reserved, count, total = struct.unpack_from('<2H2I', chunk)
                payload = total - chunk_header
                expected = {0xcac1: count * block, 0xcac2: 4, 0xcac3: 0, 0xcac4: 4}.get(kind)
                if expected is None or payload != expected or (kind == 0xcac4 and count):
                    raise ValueError('Invalid sparse chunk payload')
                counted += count
                stream.seek(payload, 1)
                if stream.tell() > path.stat().st_size:
                    raise ValueError('Sparse chunk exceeds input length')
            if counted != blocks or stream.tell() != path.stat().st_size:
                raise ValueError('Sparse image count or file length mismatch')
            sparse = True
        else:
            stream.seek(1024 + 56)
            if stream.read(2) != b'\x53\xef':
                raise ValueError('Expected ext4 or Android sparse system image')
            expanded = path.stat().st_size
            sparse = False
    if not expanded or expanded > limit:
        raise ValueError('Expanded system image exceeds measured GPT partition')
    return dict(bytes=path.stat().st_size, sha256=sha256(path), sparse=sparse,
                expanded_bytes=expanded, partition_bytes=limit)


def apex_payload_format(archive):
    with archive.open('apex_payload.img') as payload:
        header = payload.read(4096)
    if header[1024:1028] == bytes.fromhex('e2e1f5e0'):
        features = struct.unpack_from('<I', header, 1104)[0]
        block = 1 << header[1036]
        if features & ~1 or block != 4096:
            raise ValueError(f'APEX EROFS needs unsupported features/block size: {features:#x}/{block}')
        return dict(filesystem='erofs', block_bytes=block, incompat_features=features,
                    kernel_incompat_mask=1, source_format_check_passed=True,
                    runtime_mount_passed=False)
    if header[1080:1082] == b'\x53\xef':
        return dict(filesystem='ext4', runtime_mount_passed=False,
                    note='Recognized ext4; runtime mount remains required')
    raise ValueError('Unrecognized APEX payload filesystem')


def inspect_apex(path):
    before = path.stat()
    with zipfile.ZipFile(path) as container:
        if path.suffix == '.capex':
            with container.open('original_apex') as original, zipfile.ZipFile(original) as archive:
                result = apex_payload_format(archive)
        else:
            result = apex_payload_format(container)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('APEX changed during inspection: ' + str(path))
    return dict(path=str(path), bytes=after.st_size, **result)


def inspect_installed_apexes(out):
    results = []
    for directory in ('system/apex', 'system/product/apex', 'system/system_ext/apex', 'system/vendor/apex'):
        for path in sorted((out / directory).glob('*')):
            if path.is_file() and path.suffix in ('.apex', '.capex'):
                results.append(inspect_apex(path))
    if not results:
        raise ValueError('No installed APEX files found for the full product')
    return results


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('vars', 'images'):
        raise SystemExit('Usage: verify_full_images.py vars VARS | images VARS REPORT INTEGRATION')
    if not __debug__: raise RuntimeError('Optimized Python forbidden')
    values = variables(Path(sys.argv[2]))
    if sys.argv[1] == 'vars':
        print('Actual SDK37 ASUS full-product variables match measured static GPT.')
        return
    if len(sys.argv) != 5:
        raise SystemExit('images requires a new report and exact integration receipt')
    out = Path(values['PRODUCT_OUT'])
    report = dict(variables=values,
                  boot=inspect_boot(out / 'boot.img', int(values['BOARD_BOOTIMAGE_PARTITION_SIZE']), json.loads(Path(sys.argv[4]).read_text())['kernel_sha256']),
                  system=inspect_system(out / 'system.img', int(values['BOARD_SYSTEMIMAGE_PARTITION_SIZE'])),
                  installed_apex_format_checks=inspect_installed_apexes(out),
                  flash_ready=False, device_accessed=False,
                  next='Review MTK packaging, init/HAL/data compatibility and controlled hardware test')
    with Path(sys.argv[3]).open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
