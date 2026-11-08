#!/usr/bin/env python3
"""Local packaging only: original ASUS kernel plus the exact corrected SD ramdisk."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
PREVIOUS = WORK / '2026-11-07-asus-sd-media-flag-probe'
FORMAT = WORK / '2026-11-06-asus-minimal-ram-usb-probe/source/bootformat.py'
STOCK = WORK / '2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
CORRECTED = PREVIOUS / 'artifacts/candidate.img'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(data):
    return dict(bytes=len(data), sha256=sha(data))


def main():
    for name in ('source', 'artifacts', 'evidence'):
        (ROOT / name).mkdir(exist_ok=True)
    source = FORMAT.read_bytes()
    assert sha(source) == '3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017'
    shutil.copy2(FORMAT, ROOT / 'source/bootformat.py')
    spec = importlib.util.spec_from_file_location('stock_bootformat', ROOT / 'source/bootformat.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    stock, corrected = STOCK.read_bytes(), CORRECTED.read_bytes()
    assert len(stock) == b.PARTITION_SIZE and sha(stock) == b.RECOVERY_SHA
    assert len(corrected) == 8044544 and sha(corrected) == '999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510'
    header, kernel, _, _ = b.parse_image(stock)
    _, previous_kernel, ramdisk, tail = b.parse_image(corrected)
    # The supplied 7c7051... pin conflicts with the exact full stock input.
    # Existing stock-input-pins.json also pins these original bytes as b0e5d4... .
    assert not tail and sha(kernel) == 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
    assert kernel != previous_kernel
    image = b.make_image(header, kernel, ramdisk)
    padded = image + bytes(b.PARTITION_SIZE - len(image))
    (ROOT / 'artifacts/candidate.img').write_bytes(image)
    (ROOT / 'artifacts/candidate.p10.raw').write_bytes(padded)
    # Parse the actual written outputs; only Android sizes/id may change in the header.
    actual = (ROOT / 'artifacts/candidate.img').read_bytes()
    h, k, r, rest = b.parse_image(actual)
    assert not rest and k == kernel and r == ramdisk
    assert h[:8] == header[:8] and h[12:16] == header[12:16]
    assert h[20:576] == header[20:576] and h[608:] == header[608:]
    assert (ROOT / 'artifacts/candidate.p10.raw').read_bytes() == padded
    raw, extra = b.ungzip(ramdisk[512:])
    entries = b.parse_cpio(raw)
    assert not extra and set(entries) == {'init', 'dev', 'proc', 'sys', 'sd'}
    init = entries['init'][3]
    assert b'dbbb6afb-dd70-4c35-961e-9c977d7164a8\n' in init
    # These are the only installer edits. All transport/execute/locking code stays exact.
    original = (PREVIOUS / 'source/install.py').read_text()
    edits = {
        "IMAGE_SHA='999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510'": f"IMAGE_SHA='{sha(image)}'",
        "FULL_SHA='7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09'": f"FULL_SHA='{sha(padded)}'",
        "'78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9')": "'78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9','7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09')",
        'len(image)==8044544': f'len(image)=={len(image)}',
    }
    installer = original
    for old, new in edits.items():
        assert installer.count(old) == 1
        installer = installer.replace(old, new)
    (ROOT / 'source/install.py').write_text(installer)
    copies = {}
    for name in ('adb', 'legacy_adb.py'):
        src, dst = PREVIOUS / 'source' / name, ROOT / 'source' / name
        shutil.copy2(src, dst)
        assert src.read_bytes() == dst.read_bytes()
        copies[name] = record(dst.read_bytes())
    receipt = dict(
        status='LOCAL_PACKAGED_NO_PHYSICAL_TEST',
        inputs={str(STOCK.relative_to(WORK)): record(stock), str(CORRECTED.relative_to(WORK)): record(corrected)},
        image=record(actual), p10=record(padded),
        wrapped_stock_kernel=record(k), corrected_linux49_wrapped_kernel=record(previous_kernel),
        supplied_wrapped_stock_kernel_pin='7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4',
        supplied_wrapped_stock_kernel_pin_matches=False,
        wrapped_ramdisk=record(r), init=record(init),
        preservation=dict(stock_kernel_byte_identical=True, corrected_wrapped_ramdisk_byte_identical=True,
                          stock_header_unchanged_except_sizes_and_android_id=True,
                          kernel_and_dt_mutated=False, ramdisk_recompressed=False,
                          installer_only_four_literal_replacements=True,
                          execute_and_Transport_unchanged=True, adb_copies=copies),
        marker=dict(name='PROBE.ID', exact_ascii_contents='dbbb6afb-dd70-4c35-961e-9c977d7164a8\n'),
        report='PROBE.TXT', probe_lifecycle_seconds=60,
        sd_paths=['/sys/class/block/mmcblk1', '/sys/class/block/mmcblk1p1', '/dev/sd-report', '/sd'],
        actual_uname_recorded_by_unchanged_pid1=True,
        stock_recovery_binary_in_initramfs=False, stale_bcb_or_wipe_args_parsed=False,
        prior_trial_context='Parent reports manual and USB-ADB recovery trials returned healthy stock Android without PROBE.TXT; last root-read absence 2026-11-07 12:59 UTC. Not re-observed here.',
        compilation=False, hardware_contact=False, physical_boot_proven=False,
        failure_cause_proven=False,
    )
    owned = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert owned < 48 * 1024 * 1024
    receipt['owned_bytes_before_receipt'] = owned
    (ROOT / 'evidence/packaging-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ('status', 'image', 'p10', 'wrapped_stock_kernel', 'corrected_linux49_wrapped_kernel', 'wrapped_ramdisk')}, indent=2))


if __name__ == '__main__':
    main()
