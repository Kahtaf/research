"""One parent-owned targeted build; preserve r7 and continuously hold its lock."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import struct
import subprocess
import traceback
import zipfile

ROOT = Path('/srv/android/asus-runtime-prerequisite-build-r1')
AOSP = Path('/srv/android/lineage24')
LOGS = Path('/srv/android/asus-device-product/logs')
TARGETS = [
    'out/target/product/p00a/system/bin/boringssl_self_test32',
    'out/target/product/p00a/system/bin/boringssl_self_test64',
    'out/target/product/p00a/system/apex/com.android.runtime.apex',
    'out/target/product/p00a/system/build.prop',
    'out/target/product/p00a/system/system_ext/build.prop',
    'out/target/product/p00a/system/product/build.prop',
    'out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt',
]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def put(name, value):
    with (ROOT / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def native_jobs():
    jobs = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            name = (process / 'comm').read_text().strip()
            if name in ('siso', 'ninja', 'soong_ui', 'soong_build', 'ckati'):
                jobs.append({'pid': int(process.name), 'comm': name})
        except OSError:
            pass
    return jobs


def sources():
    paths = [
        'device/asus/p00a/BoardConfig.mk', 'device/asus/p00a/device.mk',
        'device/asus/p00a/lineage_p00a.mk', 'device/asus/p00a/sensors/BoardConfig.mk',
        'device/asus/p00a/firstboot/firstboot-services.mk',
        'device/asus/p00a/sepolicy/vendor/file_contexts',
        'system/vold/model/PublicVolume.cpp', 'system/memory/lmkd/lmkd.cpp',
        'external/boringssl/Android.bp', 'bionic/apex/Android.bp',
    ]
    return {name: sha(AOSP / name) for name in paths}


def prior():
    paths = sorted(LOGS.glob('full-build-r7.*'))
    paths += sorted(p for p in Path('/srv/android/asus-reviewed-build-kit/r7/attempt').rglob('*') if p.is_file())
    return {str(path): sha(path) for path in paths}


def outputs():
    result = {}
    for name in TARGETS:
        path = AOSP / name
        row = {'exists': path.is_file() and not path.is_symlink()}
        if row['exists']:
            row.update(bytes=path.stat().st_size, sha256=sha(path))
            if 'boringssl_self_test' in name:
                with path.open('rb') as stream:
                    header = stream.read(20)
                expected_class, expected_machine = (1, 40) if name.endswith('32') else (2, 183)
                row['expected_elf_architecture'] = (header[:4] == b'\x7fELF' and
                    header[4:6] == bytes([expected_class, 1]) and
                    struct.unpack_from('<H', header, 18)[0] == expected_machine)
            if name.endswith('.apex'):
                with zipfile.ZipFile(path) as archive:
                    row['zip_members'] = archive.namelist()
                    row['apex_structure_present'] = all(member in row['zip_members'] for member in
                        ('apex_manifest.pb', 'apex_payload.img', 'apex_pubkey'))
        result[name] = row
    return result


def main():
    assert Path(__file__).resolve() == ROOT / 'supervise.py'
    with (LOGS / 'full-product-build.lock').open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == 15018964
        assert not native_jobs(), native_jobs()
        assert (LOGS / 'full-build-r7.exit-code').read_text().strip() == '1'
        assert (LOGS / 'full-build-r7.finished').is_file()
        assert not (LOGS / 'full-build-r7.complete').exists()
        assert sha(LOGS / 'full-build-r7.log') == 'e18314db5121a830f0f000f8c40616e2377312a804e22e477ae20030472bdc61'
        before, prior_before = sources(), prior()
        assert before['device/asus/p00a/sensors/BoardConfig.mk'] == '9207c304761cf86afb423641534ed383e7f8dae613e64061e972d2f65832aa4d'
        assert before['system/vold/model/PublicVolume.cpp'] == 'c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9'
        put('started.json', {'utc': utc(), 'supervisor_pid': os.getpid(), 'lock_inode': 15018964,
            'targets': TARGETS, 'source_pins': before, 'r7_preservation': prior_before,
            'source_edits': False, 'installclean': False, 'full_partition_images_requested': False})
        environment = dict(os.environ, SERVICE_BUILD_LOCK_FD=str(lock.fileno()), PYTHONDONTWRITEBYTECODE='1')
        with (ROOT / 'native-build.log').open('xb') as log:
            child = subprocess.Popen(['bash', str(ROOT / 'build-targets.sh')], cwd=AOSP,
                env=environment, stdout=log, stderr=subprocess.STDOUT, pass_fds=(lock.fileno(),))
            put('native-child.json', {'utc': utc(), 'pid': child.pid, 'supervisor_pid': os.getpid()})
            code = child.wait()
        put('native-exit.json', {'utc': utc(), 'pid': child.pid, 'exit_code': code})
        unchanged = before == sources() and prior_before == prior()
        produced = outputs()
        valid = all(row['exists'] and row['bytes'] > 0 and row.get('expected_elf_architecture', True)
                    and row.get('apex_structure_present', True) for row in produced.values())
        put('finished.json', {'utc': utc(), 'exit_code': code, 'selected_sources_and_r7_unchanged': unchanged,
            'outputs': produced, 'required_structures_present': valid,
            'runtime_execution_qualified': False, 'full_os_flash_ready': False})
        assert unchanged, 'Selected source or preserved r7 evidence changed'
        assert code == 0 and valid, 'Native build or required output verification failed; preserve, no retry'


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        try:
            put('supervisor-error.json', {'utc': utc(), 'traceback': traceback.format_exc()})
        except OSError:
            pass
        raise
