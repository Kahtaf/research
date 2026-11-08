"""Admit only an actual final_package.py product; no device or process operations."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import stat
import sys

sys.dont_write_bytecode = True
WORK = Path(__file__).resolve().parents[2]
CORE = WORK / '2026-11-07-asus-offline-stock-fallback'
DEFAULT_ASSEMBLY = CORE / 'artifacts/final'
KERNEL = WORK / '2026-11-06-asus-bmc156-full-kernel/artifacts/Image.gz-dtb'
DELIVERY_SHA = '0683c8974b9b11b0ec2b752543fc702920f76527e48ba1ef6c447784a8afef6c'
SOURCE_PINS = {
    'scripts/final_package.py': '382b753f9c0af7bad1f821a468c6e6ec5541544603b1a0ca2a9ee54efa7fecee',
    'source/bootformat.py': '3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017',
    'source/fdt.py': '1bd710a08eae5677689a52042a621f39dcd57e49197749cf2833eead1fc0dcae',
    'source/lk_contract.py': '34331d6eef8254e2b17b8464dc73997bd582826f6008bf2efd8a5561879b32d7',
    'source/boot_memory.py': '4efe28cf150856c86b7b851464b40ad9dd05fa0daaab6502694fa1083cf37575',
    'source/package_core.py': '442f6e099999d83ccd77eab2e10c4cfc935c206e908a364acfbd56c96771329b',
    'source/init.offline.action.rc': '6d38d8a9daaf3b75136f730c900bbf6776bdb04b514c8574ece4db8859b7b93b',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def nonsymlink(path):
    path = Path(path).absolute()
    need(not any(p.is_symlink() for p in (path, *path.parents)),
         'Nonsymlink input path required: ' + str(path))
    return path


def ordinary(path, limit):
    path = nonsymlink(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit,
             'Bounded ordinary input required: ' + str(path))
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(limit + 1)
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        need(len(data) == before.st_size and
             all(getattr(before, f) == getattr(after, f) for f in fields),
             'Input changed during read: ' + str(path))
        return data
    finally:
        os.close(fd)


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def parse_receipt(raw):
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    need(type(value) is dict, 'Assembly receipt must be an object')
    need(value.get('status') == 'ASSEMBLED_NOT_PHYSICALLY_QUALIFIED',
         'Actual unqualified final assembly receipt required')
    for field in ('image_sha256', 'p10_sha256', 'manifest_sha256', 'arm_id'):
        text = value.get(field)
        need(type(text) is str and len(text) == 64 and
             all(c in '0123456789abcdef' for c in text) and text != '0' * 64,
             'Actual assembly digest/arm required: ' + field)
    need(type(value.get('image_bytes')) is int and 2048 < value['image_bytes'] < 16740352
         and type(value.get('p10_bytes')) is int and value['p10_bytes'] == 16740352,
         'Exact image/full-p10 geometry required')
    need(value.get('physical_boot_verified') is False and value.get('sd_hardware_verified') is False,
         'Assembly receipt is not physical GO')
    return value


def check_sources():
    need(sha(ordinary(CORE / 'evidence/DELIVERY_PINS.json', 65536)) == DELIVERY_SHA,
         'Final core delivery pins changed')
    for relative, pin in SOURCE_PINS.items():
        need(sha(ordinary(CORE / relative, 1024 * 1024)) == pin,
             'Final core admission source changed: ' + relative)


def load_core():
    need(__debug__, 'Run without Python optimization; reviewed parsers require assertions')
    check_sources()
    # Load exactly the pinned parsers before the packager imports them by name.
    for name in ('bootformat', 'fdt', 'lk_contract', 'boot_memory', 'package_core'):
        path = CORE / 'source' / (name + '.py')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        source = ordinary(path, 1024 * 1024)
        need(sha(source) == SOURCE_PINS['source/' + name + '.py'], 'Parser source changed at load')
        exec(compile(source, str(path), 'exec'), module.__dict__)
    path = CORE / 'scripts/final_package.py'
    spec = importlib.util.spec_from_file_location('final_assembly_contract', path)
    module = importlib.util.module_from_spec(spec)
    source = ordinary(path, 1024 * 1024)
    need(sha(source) == SOURCE_PINS['scripts/final_package.py'], 'Packager source changed at load')
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module


def admit(directory):
    """Only reads bounded public assembly products; never reads raw role images."""
    directory = nonsymlink(directory)
    need(directory.is_dir(), 'Actual parent final assembly directory required: ' + str(directory))
    receipt_raw = ordinary(directory / 'assembly.json', 65536)
    receipt = parse_receipt(receipt_raw)
    f = load_core()
    b = f.b
    pins = json.loads(ordinary(CORE / 'evidence/DELIVERY_PINS.json', 65536))

    def core_input(relative, limit):
        data = ordinary(CORE / relative, limit)
        need(sha(data) == pins[relative], 'Delivered final core input changed: ' + relative)
        return data

    image = ordinary(directory / 'candidate.img', b.PARTITION_SIZE)
    full = ordinary(directory / 'candidate.p10.raw', b.PARTITION_SIZE)
    need(len(image) == receipt['image_bytes'] and sha(image) == receipt['image_sha256'],
         'Receipt/candidate image mismatch')
    need(len(full) == receipt['p10_bytes'] and sha(full) == receipt['p10_sha256'] and
         full == image + bytes(b.PARTITION_SIZE - len(image)),
         'Receipt/full-p10/zero-padding mismatch')
    _, _, ramdisk, tail = b.parse_image(image)
    need(not tail, 'Candidate must end at aligned ramdisk boundary')
    members = ordinary(directory / 'operational-ramdisk.members', 4 * 1024**2)
    need(ramdisk[512:] == members, 'Operational ramdisk file differs from candidate')
    raw_cpio, _ = b.ungzip(members, 16 * 1024**2)
    entries = b.parse_cpio(raw_cpio)
    manifest_entry = entries.get('rescue.manifest')
    arm_entry = entries.get('rescue.sd.arm')
    need(manifest_entry is not None and arm_entry is not None,
         'Actual embedded five-role manifest and arm required')
    manifest, arm = manifest_entry[3], arm_entry[3]
    need(manifest_entry[:3] == (0o100444, 0, 0) and len(manifest) <= 1024**2 and
         arm_entry[:3] == (0o100444, 0, 0) and arm == (receipt['arm_id'] + '\n').encode(),
         'Immutable actual manifest/arm shape required')
    roles = f.five_roles(manifest)
    original = core_input('inputs/original-stock.manifest', 128 * 1024)
    need(manifest[16:112] == original[16:112] and
         manifest[112:len(original)] == original[112:],
         'Exact genuine original-pair prefix required')
    need(roles == receipt.get('roles') and sha(manifest) == receipt['manifest_sha256'],
         'Receipt/actual five-role manifest mismatch')

    # Reproduce the existing byte join in RAM using actual embedded authorities,
    # the pinned common rootfs and the public physical e9 kernel. No output/build.
    common = core_input('artifacts/common-rootfs.cpio.gz', 4 * 1024**2)
    expected_entries = b.parse_cpio(f.gzip.decompress(common))
    need('rescue.manifest' not in expected_entries and 'rescue.sd.arm' not in expected_entries,
         'Common core already has final authority')
    expected_entries['rescue.manifest'] = (0o100444, 0, 0, manifest)
    expected_entries['rescue.sd.arm'] = (0o100444, 0, 0, arm)
    expected_entries['init.rc'] = (0o100644, 0, 0,
        expected_entries['init.rc'][3] + b'\n' + ordinary(CORE / 'source/init.offline.action.rc', 65536))
    need(entries == expected_entries, 'Final operational RAM tree differs from completed core')
    kernel = ordinary(KERNEL, 8 * 1024**2)
    expected_image, expected_members, contract = f.package(
        expected_entries, kernel, core_input('inputs/original-header', 2048),
        core_input('inputs/original-kernel-wrapper', 512), core_input('inputs/original-wrapper', 512))
    need(image == expected_image and members == expected_members and receipt.get('packaging') == contract,
         'Physical e9 kernel/header/wrappers/layout/binding contract mismatch')
    # This also proves the sole canonical second newc member and its zero padding.
    binding = ordinary(directory / 'rescue.current.binding', 144)
    capsule = b.parse_cpio(members[contract['core_gzip_bytes']:])
    need(capsule == {'rescue.current.binding': (0o100444, 0, 0, binding)} and
         len(binding) == 144 and sha(binding) == contract['binding_sha256'],
         'Exact immutable current binding required')
    expected_receipt = dict(status='ASSEMBLED_NOT_PHYSICALLY_QUALIFIED',
        manifest_sha256=sha(manifest), arm_id=arm[:64].decode(), roles=roles,
        image_sha256=sha(image), image_bytes=len(image), p10_sha256=sha(full), p10_bytes=len(full),
        packaging=contract, normal_graph_keeps_custom_recovery=True,
        original_recovery_helper_included=True, stock_profile_selectable=True,
        stock_success_outcome='OEM_RESET_REQUIRED', stock_success_reboot='POWER_OFF',
        physical_boot_verified=False, sd_hardware_verified=False)
    need(json.dumps(receipt, sort_keys=True) == json.dumps(expected_receipt, sort_keys=True),
         'Final assembly behavior/receipt contract mismatch')
    prefix = b'OFFLINE-PREARMED ASUSR002 ' + sha(manifest).encode() + b' ' + arm[:64]
    mode = b'OFFLINE-SELECT ASUSR002 ' + sha(manifest).encode() + b' ' + arm[:64]
    controls = {
        'manifest.sha256': sha(manifest).encode() + b'\n',
        'execute.trigger': prefix + b' install:2,4,3\n',
        'system.trigger': prefix + b' rollback:0:inverse:-1\n',
        'boot.trigger': prefix + b' rollback:1:inverse:-1\n',
        'asus-rescue.mode.install': mode + b' INSTALL\n',
        'asus-rescue.mode.stock': mode + b' STOCK-RESTORE\n',
    }
    for name, expected in controls.items():
        need(ordinary(directory / name, 1024) == expected, 'Assembly control mismatch: ' + name)
    return full, dict(assembly_directory=str(directory), assembly_sha256=sha(receipt_raw),
        candidate_sha256=sha(image), full_p10_sha256=sha(full),
        manifest_sha256=sha(manifest), arm_id=receipt['arm_id'],
        binding_sha256=sha(binding), physical_GO=False, hardware_ready=False)
