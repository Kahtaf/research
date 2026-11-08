"""Small filesystem/process behavior fixtures. Never use the production plan."""
import contextlib
import ctypes
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import integrate as i
import verify_full_images as v
from validate_completed_product import materialize, verify_source_images
from verify_root_payload import verify as verify_root, verify_ramdisk_properties
from verify_input_payload import verify as verify_input, INSTALLED
sys.path.insert(0, str(ROOT / 'tests/packager/scripts'))
sys.path.insert(0, str(ROOT / 'tests/packager/probe'))
import package_full_boot as packager
from bootformat import make_cpio, pad, boot_id
from lk_contract import REQUIRED_INPUT


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode() if isinstance(value, str) else value)
    return path

def jsonput(path, value): return put(path, json.dumps(value))


class Fixture:
    def __init__(self, root):
        self.root = root
        self.k = root / 'active-kernel'
        self.k.mkdir()
        for n in range(268): put(self.k / ('src/' + str(n)), 'before-' + str(n))
        subprocess.run(['git', 'init', '-q', str(self.k)], check=True)
        subprocess.run(['git', '-C', str(self.k), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.k), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid', 'commit', '-qm', 'TEST_ONLY'], check=True)
        baseline = {p: x['sha256'] for p, x in i.manifest(self.k / 'src').items()}
        baseline = {'src/' + p: h for p, h in baseline.items()}
        head = subprocess.check_output(['git', '-C', str(self.k), 'rev-parse', 'HEAD'], text=True).strip()
        compiled = root / 'compiled'
        changes = {}
        for n in range(268):
            p = 'src/' + str(n)
            put(self.k / p, 'after-' + str(n))
            put(compiled / p, 'after-' + str(n))
            changes[p] = {'before': baseline[p], 'after': i.sha(compiled / p)}
        diff = subprocess.check_output(['git', '-C', str(self.k), 'diff', '--binary'])
        subprocess.run(['git', '-C', str(self.k), 'restore', '.'], check=True)
        patchfile = put(root / 'inputs/kernel.patch', diff)
        device = root / 'device'
        put(device / 'BoardConfig.mk', 'old board')
        put(device / 'prebuilt/Image.gz-dtb', 'old kernel')
        put(device / 'untouched', 'keep')
        put(device / 'device.mk', 'original product\n')
        before = i.manifest(device)
        staging = root / 'staging'
        candidate = staging / 'product-device'
        shutil.copytree(device, candidate)
        put(candidate / 'BoardConfig.mk', 'combined board')
        put(candidate / 'prebuilt/Image.gz-dtb', 'combined kernel')
        for n in range(22): put(candidate / ('radio/change-' + str(n)), 'radio-' + str(n))
        put(candidate / 'device.mk', 'radio product\n')
        put(candidate / 'radio/wificond.rc', 'new wificond')
        after = i.manifest(candidate)
        radio_after = dict(after)
        radio_after['prebuilt/Image.gz-dtb'] = before['prebuilt/Image.gz-dtb']
        radio_after['BoardConfig.mk'] = {'sha256': hashlib.sha256(b'radio board').hexdigest()}
        radio_changes = {p: {'before': before.get(p), 'after': h} for p, h in radio_after.items() if before.get(p) != h}
        assert len(radio_changes) == 25
        base_mk = (candidate / 'device.mk').read_bytes()
        base_mk_path = put(root / 'inputs/base-radio-device.mk', base_mk)
        put(candidate / 'device.mk', base_mk + i.INPUT_SUFFIX)
        for rel in i.INPUT_FILES:
            put(candidate / rel, (ROOT / 'inputs/input-files' / rel).read_bytes())
        after = i.manifest(candidate)
        input_delta = {'files': i.INPUT_FILES, 'device_mk_before_sha256': i.sha(base_mk_path),
                       'device_mk_after_sha256': after['device.mk']['sha256'], 'suffix': i.INPUT_SUFFIX.decode()}
        input_receipt = jsonput(root / 'inputs/input-mapping.json', input_delta)
        connectivity = root / 'Connectivity'
        conn_before = {}
        conn_after = {}
        for rel in ['bpf/loader/NetBpfLoad.cpp', 'bpf/netd/BpfHandler.cpp', 'bpf/progs/netd.c']:
            conn_before[rel] = i.sha(put(connectivity / rel, 'before ' + rel))
            conn_after[rel] = i.sha(put(staging / 'platform-connectivity' / rel, 'after ' + rel))
        config = put(staging / 'kernel-config/asus_p00a_combined_defconfig', 'CONFIG_FILE_LOCKING=y\nCONFIG_BLK_CGROUP=y\n')
        staged = {'product_before': before, 'product_after': after, 'connectivity': {p: {'sha256': h} for p, h in conn_after.items()}, 'kernel_config_sha256': i.sha(config)}
        receipts = {
            'staged': staged,
            'parity': {'firstboot_file_locking_parity_accepted': True, 'combined_kernel_sha256': after['prebuilt/Image.gz-dtb']['sha256'], 'parent_actual_source_and_config_check': {'staged_config_sha256': i.sha(config)}},
            'source': {'changes': changes, 'base_commit': head, 'patch_sha256': i.sha(patchfile)},
            'radio': {'before': before, 'after': radio_after, 'changes': radio_changes},
            'network': {'connectivity_before': conn_before, 'connectivity_after': conn_after},
            'snapshot': {'files': baseline, 'head': head}}
        receipt_paths = {name: str(jsonput(root / 'inputs' / (name + '.json'), data)) for name, data in receipts.items()}
        logs = root / 'logs'
        logs.mkdir()
        product = root / 'out'
        product.mkdir()
        put(product / 'boot.img', 'small TEST_ONLY boot')
        put(product / 'system.img', 'small TEST_ONLY system')
        now = datetime.datetime.now(datetime.timezone.utc)
        for name, seconds in [('started', -3), ('complete', -2), ('finished', -1)]:
            put(logs / ('full-build-r5.' + name), (now + datetime.timedelta(seconds=seconds)).isoformat() + '\n')
        put(logs / 'full-build-r5.exit-code', '0\n')
        put(logs / 'full-build-r5.log', 'TEST_ONLY successful build\n')
        jsonput(logs / 'full-build-r5.images.json', {'variables': {'PLATFORM_SDK_VERSION': '37'}, 'boot': {'sha256': i.sha(product / 'boot.img')}, 'system': {'sha256': i.sha(product / 'system.img')}})
        wificond = put(root / 'wificond.rc', 'original wificond')
        link = root / 'kernel-link'
        link.symlink_to(self.k)
        self.plan = {
            'revision': 'r6', 'original_pids': [], 'run_root': str(root), 'logs': str(logs),
            'lock': str(put(logs / 'full-product-build.lock', b'')), 'product_out': str(product),
            'kernel': str(self.k), 'kernel_link': str(link), 'compiled_fixture': str(compiled),
            'device': str(device), 'connectivity': str(connectivity), 'staging': str(staging),
            'wificond': str(wificond), 'wificond_before': i.sha(wificond),
            'defconfig': str(self.k / 'arch/arm64/configs/asus_p00a_combined_defconfig'),
            'config': str(config), 'kernel_release': str(put(root / 'inputs/kernel.release', '4.9.TEST_ONLY\n')),
            'patch': str(patchfile), 'external_pins': {str(config): i.sha(config), str(patchfile): i.sha(patchfile)},
            'clean_receipt': str(put(logs / 'full-product-installclean.complete', 'prior only\n')),
            'input_mapping_receipt': str(input_receipt), 'input_mapping_base': str(base_mk_path),
            **{name + '_receipt': receipt_paths[name] for name in ['staged', 'parity', 'source', 'radio', 'network']},
            'snapshot': receipt_paths['snapshot']}
        self.receipts = receipts
        # Fixture launcher exercises actual FD inheritance/lock contention. It has
        # no AOSP command and cannot be selected by the production CLI.
        put(root / 'scripts/build.sh', '''#!/bin/bash
set -e
python3 -B - "$1" <<'CHILD'
import fcntl,json,os,sys,hashlib
from pathlib import Path
r=Path(sys.argv[1]); p=json.loads((r/'inputs/fixture-plan.json').read_text())
fd=int(os.environ['REVIEWED_BUILD_LOCK_FD'])
assert os.fstat(fd).st_ino == Path(p['lock']).stat().st_ino
with open(p['lock'],'r+') as independent:
 try: fcntl.flock(independent,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError: pass
 else: raise RuntimeError('lock gap')
with (r/'attempt/fixture-launched').open('x') as f:f.write('one launch under inherited lock')
(r/'attempt/validation').mkdir()
(r/'attempt/validation/complete.json').write_text(json.dumps({'flash_ready':False,'integration_receipt_sha256':hashlib.sha256((r/'attempt/integration.json').read_bytes()).hexdigest()}))
CHILD
''')
        jsonput(root / 'inputs/fixture-plan.json', self.plan)
        self.seal()

    def seal(self):
        pins = {str(p.relative_to(self.root)): i.sha(p) for p in (self.root / 'inputs').glob('*') if p.name != 'kit-pins.json'}
        pins['scripts/build.sh'] = i.sha(self.root / 'scripts/build.sh')
        jsonput(self.root / 'inputs/kit-pins.json', pins)


class KitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='TEST_ONLY-', dir=ROOT / 'tests')
        self.root = Path(self.tmp.name)
        self.f = Fixture(self.root)
        self.p = self.f.plan

    def tearDown(self): self.tmp.cleanup()

    def audit(self): return i.audit_inputs(self.p, baseline=False)

    def execute(self, active=False):
        actual = i.audit_inputs
        # Only skip the 61,976-file production baseline in these bounded fixtures;
        # every changed preimage, artifact, copy, git patch and lock remains real.
        with patch.object(i, 'native_processes', return_value=[]), patch.object(i, 'audit_inputs', side_effect=lambda p: actual(p, baseline=False)):
            return i.execute(self.p, self.root, active)

    def test_exact_manifest_and_no_active_mutation_in_plan(self):
        before = i.manifest(self.f.k)
        out = self.execute()
        self.assertEqual(out['mode'], 'PLAN_ONLY')
        self.assertEqual(before, i.manifest(self.f.k))
        self.assertFalse((self.root / 'attempt').exists())
        self.assertEqual(out['audit']['radio_changes'], 25)
        self.assertEqual(out['audit']['connectivity_files'], 3)
        self.assertEqual(out['audit']['input_mapping_files'], 3)

    def test_input_inheritance_cannot_hide_extra_make_changes_in_manifest(self):
        path = Path(self.p['staging']) / 'product-device/device.mk'
        path.write_bytes(path.read_bytes() + b'PRODUCT_PACKAGES += unreviewed\n')
        staged = self.f.receipts['staged']
        staged['product_after']['device.mk'] = i.item(path)
        jsonput(self.p['staged_receipt'], staged)
        delta = i.read(self.p['input_mapping_receipt'])
        delta['device_mk_after_sha256'] = i.sha(path)
        jsonput(self.p['input_mapping_receipt'], delta)
        with self.assertRaisesRegex(i.Refusal, 'exact additive line'): self.audit()

    def test_input_mapping_cannot_be_rebound_to_altered_bytes(self):
        rel = 'input/mtk-kpd.kl'
        path = Path(self.p['staging']) / 'product-device' / rel
        put(path, 'key 116 VOLUME_DOWN\n')
        staged = self.f.receipts['staged']
        staged['product_after'][rel] = i.item(path)
        jsonput(self.p['staged_receipt'], staged)
        delta = i.read(self.p['input_mapping_receipt'])
        delta['files'][rel] = i.sha(path)
        jsonput(self.p['input_mapping_receipt'], delta)
        with self.assertRaisesRegex(i.Refusal, 'Input mapping selection changed'): self.audit()

    def test_live_lock_refuses_before_any_attempt_or_source_edit(self):
        with open(self.p['lock'], 'r+') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(i.Refusal, 'LIVE_BUILD_LOCK'): self.execute(True)
        self.assertFalse((self.root / 'attempt').exists())
        self.assertEqual((self.f.k / 'src/0').read_text(), 'before-0')

    @unittest.skipUnless(sys.platform == 'linux', 'actual /proc native identity fixture is Linux-only')
    def test_real_native_process_refuses_before_mutation(self):
        child = subprocess.Popen([sys.executable, '-B', '-c', "import ctypes,sys;ctypes.CDLL(None).prctl(15,b'ninja',0,0,0);print('READY',flush=True);sys.stdin.read()"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'READY')
            self.assertTrue(any(row['pid'] == child.pid for row in i.native_processes(self.p)))
            with self.assertRaisesRegex(i.Refusal, 'LIVE_NATIVE_BUILD'): i.execute(self.p, self.root, True)
            self.assertFalse((self.root / 'attempt').exists())
        finally:
            child.communicate('done', timeout=5)

    def test_missing_and_mutated_kernel_preimage_refused(self):
        path = self.f.k / 'src/0'
        path.unlink()
        with self.assertRaisesRegex(i.Refusal, 'Kernel preimage'): self.audit()
        path.write_text('changed')
        with self.assertRaisesRegex(i.Refusal, 'Kernel preimage'): self.audit()

    def test_missing_and_mutated_parity_receipt_pins_refused(self):
        path = Path(self.p['parity_receipt'])
        data = path.read_bytes()
        path.unlink()
        with self.assertRaises(FileNotFoundError): i.verify_pins(self.root)
        path.write_bytes(data + b' ')
        with self.assertRaisesRegex(i.Refusal, 'Kit pin changed'): i.verify_pins(self.root)
        obj = json.loads(data)
        obj['firstboot_file_locking_parity_accepted'] = False
        path.write_text(json.dumps(obj))
        with self.assertRaisesRegex(i.Refusal, 'Parent scoped parity'): self.audit()

    def test_candidate_extra_or_mutated_file_rejected(self):
        path = Path(self.p['staging']) / 'product-device/extra'
        path.write_text('unselected')
        with self.assertRaisesRegex(i.Refusal, 'Candidate product'): self.audit()
        path.unlink()
        put(Path(self.p['staging']) / 'product-device/radio/change-0', 'wrong')
        with self.assertRaisesRegex(i.Refusal, 'Candidate product'): self.audit()

    def test_config_or_patch_mutation_missing_artifact_refused(self):
        path = Path(self.p['config'])
        path.write_text('wrong')
        with self.assertRaisesRegex(i.Refusal, 'External artifact changed'): self.audit()
        path.unlink()
        with self.assertRaises(FileNotFoundError): self.audit()
        put(path, 'CONFIG_FILE_LOCKING=y\nCONFIG_BLK_CGROUP=y\n')
        put(self.p['patch'], 'mutated patch')
        with self.assertRaisesRegex(i.Refusal, 'External artifact changed'): self.audit()

    def test_connectivity_exact_three_and_preimages(self):
        put(Path(self.p['connectivity']) / 'bpf/progs/netd.c', 'wrong')
        with self.assertRaisesRegex(i.Refusal, 'Connectivity preimage'): self.audit()

    def test_unknown_prior_result_and_failed_success_incoherence(self):
        path = Path(self.p['logs']) / 'full-build-r5.exit-code'
        path.unlink()
        with self.assertRaisesRegex(i.Refusal, 'Unknown prior result'): self.execute(True)
        path.write_text('1\n')
        with self.assertRaisesRegex(i.Refusal, 'Incoherent failed prior result'): self.execute(True)
        complete = Path(self.p['logs']) / 'full-build-r5.complete'
        completedata = complete.read_text()
        complete.unlink()
        with self.assertRaisesRegex(i.Refusal, 'Prior r5 failed'): self.execute(True)
        complete.write_text(completedata)
        path.write_text('0\n')
        (Path(self.p['logs']) / 'full-build-r5.complete').unlink()
        with self.assertRaisesRegex(i.Refusal, 'Success lacks'): self.execute(True)
        self.assertFalse((self.root / 'attempt').exists())

    def test_failed_terminal_requires_exact_explicit_parent_review(self):
        put(Path(self.p['logs']) / 'full-build-r5.exit-code', '19\n')
        (Path(self.p['logs']) / 'full-build-r5.complete').unlink()
        description = i.terminal(self.p, describe=True)
        template = description['review_template']
        review = jsonput(self.root / 'parent-review/r5-failure.json', template)
        with self.assertRaisesRegex(i.Refusal, 'not explicitly reviewed'):
            i.terminal(self.p, (review, i.sha(review)))
        template['reviewed_by_parent'] = True
        template['reason'] = 'TEST_ONLY reviewed failure; next product change authorized'
        jsonput(review, template)
        accepted = i.terminal(self.p, (review, i.sha(review)))
        self.assertEqual(accepted['terminal_kind'], 'FAILED_REVIEWED_FOR_NEW_PRODUCT')
        put(Path(self.p['logs']) / 'full-build-r5.log', 'changed after parent review')
        with self.assertRaisesRegex(i.Refusal, 'changed since parent review'):
            i.terminal(self.p, (review, i.sha(review)))

    def test_prior_image_receipt_mismatch(self):
        put(Path(self.p['product_out']) / 'boot.img', 'wrong image')
        with self.assertRaisesRegex(i.Refusal, 'Prior output/report mismatch'): self.execute(True)
        self.assertFalse((self.root / 'attempt').exists())

    def test_apply_preserves_exact_sources_images_then_launches_once_under_lock(self):
        result = self.execute(True)
        self.assertEqual(result['mode'], 'PARENT_EXECUTE')
        self.assertTrue((self.root / 'attempt/fixture-launched').is_file())
        self.assertEqual((self.root / 'attempt/before/kernel/src/0').read_text(), 'before-0')
        self.assertEqual((self.root / 'attempt/before/images/system.img').read_text(), 'small TEST_ONLY system')
        self.assertEqual((self.f.k / 'src/0').read_text(), 'after-0')
        self.assertEqual(i.manifest(self.p['device']), self.f.receipts['staged']['product_after'])
        self.assertEqual(i.sha(self.p['defconfig']), i.sha(self.p['config']))
        with self.assertRaisesRegex(i.Refusal, 'Revision already used|Previous attempt'): self.execute(True)

    def test_integration_holds_lock_and_postimage_drift_rejected(self):
        real_apply = i.apply
        def locked_apply(plan, attempt):
            with open(plan['lock'], 'r+') as other:
                with self.assertRaises(BlockingIOError): fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
            real_apply(plan, attempt)
            with open(plan['lock'], 'r+') as other:
                with self.assertRaises(BlockingIOError): fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch.object(i, 'apply', side_effect=locked_apply): self.execute(True)
        put(self.f.k / 'src/0', 'mutated after build')
        with self.assertRaisesRegex(i.Refusal, 'Integrated source drift'): i.verify_integrated(self.p)

    def test_partial_apply_failure_is_preserved_and_cannot_retry(self):
        real_copy = i.copy_exact
        def fail_after_first(src, dst, expected):
            if 'radio/change-0' in str(dst): raise OSError('injected copy failure')
            return real_copy(src, dst, expected)
        with patch.object(i, 'copy_exact', side_effect=fail_after_first):
            with self.assertRaisesRegex(OSError, 'injected'): self.execute(True)
        self.assertTrue((self.root / 'attempt/FAILED.json').is_file())
        self.assertEqual((self.f.k / 'src/0').read_text(), 'after-0')
        self.assertEqual((self.root / 'attempt/before/kernel/src/0').read_text(), 'before-0')
        self.assertFalse((self.root / 'attempt/launch.json').exists())
        with self.assertRaisesRegex(i.Refusal, 'Previous attempt'): self.execute(True)

    def test_build_failure_not_marked_complete_or_retried(self):
        put(self.root / 'scripts/build.sh', '#!/bin/bash\nexit 31\n')
        self.f.seal()
        with self.assertRaisesRegex(i.Refusal, 'Build/validation failed'): self.execute(True)
        self.assertTrue((self.root / 'attempt/FAILED.json').is_file())
        self.assertFalse((Path(self.p['logs']) / 'full-build-r6.complete').exists())
        self.assertEqual((Path(self.p['logs']) / 'full-build-r6.exit-code').read_text(), '31\n')
        with self.assertRaisesRegex(i.Refusal, 'Revision already used'): self.execute(True)


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='TEST_ONLY-', dir=ROOT / 'tests')
        self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def input_tree(self, path):
        source = ROOT / 'inputs/input-files/input'
        for rel in INSTALLED:
            put(path / rel, (source / Path(rel).name).read_bytes())
        return path

    def test_installed_input_mapping_requires_exact_real_files(self):
        product = self.input_tree(self.root / 'product')
        self.assertEqual(len(verify_input(product)['checked']), 2)
        rel = next(iter(INSTALLED))
        path = product / rel
        original = path.read_bytes()
        path.write_bytes(b'touch.orientationAware=0\n')
        with self.assertRaisesRegex(i.Refusal, 'bytes differ'): verify_input(product)
        path.unlink()
        source = put(self.root / 'outside', original)
        path.symlink_to(source)
        with self.assertRaisesRegex(i.Refusal, 'missing or invalid'): verify_input(product)

    def test_real_ext4_input_mapping_bytes_and_system_root_layout(self):
        mkfs, debugfs = shutil.which('mkfs.ext4'), shutil.which('debugfs')
        if not mkfs or not debugfs: self.skipTest('actual e2fsprogs fixture requires Linux tools')
        product = self.input_tree(self.root / 'product')
        image = self.root / 'system.raw'
        with image.open('wb') as f: f.truncate(16 * 1024 * 1024)
        subprocess.run([mkfs, '-q', '-F', '-d', str(product), str(image)], check=True, capture_output=True)
        self.assertTrue(all(x['final_ext4_verified'] for x in verify_input(product, image, debugfs)['checked']))
        rel = 'system/vendor/usr/keylayout/mtk-kpd.kl'
        subprocess.run([debugfs, '-w', '-R', 'rm /' + rel, str(image)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, image, debugfs)
        bad = put(self.root / 'bad-map', 'key 116 VOLUME_DOWN\n')
        subprocess.run([debugfs, '-w', '-R', 'write ' + str(bad) + ' /' + rel, str(image)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, image, debugfs)
        flat = self.root / 'flat.raw'
        with flat.open('wb') as f: f.truncate(16 * 1024 * 1024)
        subprocess.run([mkfs, '-q', '-F', '-d', str(product / 'system'), str(flat)], check=True, capture_output=True)
        with self.assertRaisesRegex(i.Refusal, 'SYSTEM input mapping bytes differ'): verify_input(product, flat, debugfs)

    def vars_fixture(self):
        s = (ROOT / 'inputs/observed-r5.vars').read_text()
        # Only a text fixture for variable validation; never an actual product target.
        additional = 'p00a-wmt libbtcal libbt-vendor-p00a libbluetooth_mtk_p00a android.hardware.bluetooth@1.1-service.p00a wpa_supplicant P00aWifiBringupOverlay'
        lines = [line[:-1] + ' ' + additional + "'" if line.startswith('PRODUCT_PACKAGES=') else line for line in s.splitlines()]
        return '\n'.join(lines) + '\n'

    def test_adb_root_and_adbd_required_secure_userdebug(self):
        path = put(self.root / 'vars', self.vars_fixture())
        v.variables(path)
        for token in ['adb_root', 'com.android.adbd']:
            path.write_text(self.vars_fixture().replace(' ' + token + ' ', ' '))
            with self.assertRaisesRegex(ValueError, 'missing required'): v.variables(path)
        path.write_text(self.vars_fixture().replace('ro.adb.secure=1', 'ro.adb.secure=0'))
        with self.assertRaisesRegex(ValueError, 'authenticated ADB'): v.variables(path)

    def test_real_output_root_route_requires_elf_rc_apex_and_secure_props(self):
        product = self.root / 'product'
        apex = self.root / 'apex'
        elf = bytearray(64)
        elf[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', elf, 18, 183)
        put(product / 'system/system_ext/bin/adb_root', bytes(elf))
        rc = put(product / 'system/system_ext/etc/init/adb_root.rc', 'TEST_ONLY root init')
        put(product / 'system/apex/com.android.adbd.apex', 'TEST_ONLY source APEX')
        put(apex / 'com.android.adbd/bin/adbd', bytes(elf))
        metadata = put(apex / 'apex-info-list.xml', '<apex-info-list><apex-info moduleName="com.android.adbd" isActive="true" modulePath="/system/apex/com.android.adbd.apex"/></apex-info-list>')
        props = put(product / 'system/build.prop', 'ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
        result = verify_root(product, apex, i.sha(rc))
        self.assertFalse(result['root_runtime_verified'])
        props.write_text('ro.secure=0\nro.debuggable=1\nro.adb.secure=1\n')
        with self.assertRaisesRegex(i.Refusal, 'property mismatch'): verify_root(product, apex, i.sha(rc))
        props.write_text('ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
        metadata.write_text('<apex-info-list/>')
        with self.assertRaisesRegex(i.Refusal, 'exactly one adbd'): verify_root(product, apex, i.sha(rc))
        with self.assertRaisesRegex(i.Refusal, 'Insecure actual ramdisk'):
            verify_ramdisk_properties({'prop.default': (0o100644, 0, 0, b'ro.adb.secure=0\n')}, product)

    def test_zero_ranges_and_partition_tail_are_written(self):
        source = self.root / 'sparse-input'
        with source.open('wb') as f:
            f.write(b'A')
            f.seek(1024 * 1024)
            f.write(b'Z')
        out = self.root / 'raw'
        materialize(source, out, 2 * 1024 * 1024)
        self.assertEqual(out.read_bytes(), b'A' + bytes(1024 * 1024 - 1) + b'Z' + bytes(1024 * 1024 - 1))
        # Linux fixture filesystem accounting is evidence that zero writes weren't seeks.
        if sys.platform == 'linux': self.assertGreaterEqual(out.stat().st_blocks * 512, out.stat().st_size)

    def test_source_image_changes_refused(self):
        put(self.root / 'boot.img', 'actual source')
        put(self.root / 'system.img', 'actual system')
        report = {n: {'sha256': i.sha(self.root / (n + '.img'))} for n in ('boot', 'system')}
        verify_source_images(self.root, report)
        put(self.root / 'boot.img', 'mutated')
        with self.assertRaisesRegex(i.Refusal, 'Source image changed'): verify_source_images(self.root, report)

    def test_wrong_full_boot_hash_kernel_and_synthetic_rejected(self):
        kernel = b'TEST_ONLY_not_a_kernel'
        ram = gzip.compress(make_cpio({'NONBOOTABLE-SYNTHETIC-FIXTURE.txt': (0o100644, 0, 0, b'TEST ONLY')}), mtime=0)
        header = bytearray(2048)
        header[:8] = b'ANDROID!'
        struct.pack_into('<10I', header, 8, len(kernel), 0x40080000, len(ram), 0x44000000, 0, 0x40f00000, 0x4e000000, 2048, 0, 0)
        command = b' '.join(k + b'=' + x for k, x in REQUIRED_INPUT.items())
        header[64:64+len(command)] = command
        header[576:608] = boot_id(kernel, ram)
        data = bytes(header) + pad(kernel) + pad(ram)
        with self.assertRaisesRegex(ValueError, 'report hash mismatch'): packager.package(data, kernel, {'boot': {'sha256': '0' * 64}})
        report = {'boot': {'sha256': hashlib.sha256(data).hexdigest()}}
        with self.assertRaisesRegex(ValueError, 'Kernel differs'): packager.package(data, b'wrong', report)
        with self.assertRaisesRegex(ValueError, 'Synthetic fixture rejected'): packager.package(data, kernel, report)
        empty = gzip.compress(make_cpio({'file': (0o100644, 0, 0, b'no init')}), mtime=0)
        with self.assertRaisesRegex(ValueError, 'Missing first-stage init'): packager.validate_ramdisk(empty, False)

    def test_no_clean_or_unbounded_compile_command_in_build(self):
        script = (ROOT / 'scripts/build.sh').read_text()
        commands = [l.strip() for l in script.splitlines() if l.strip().startswith('m ')]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(c.startswith('m -j8 ') for c in commands))
        self.assertFalse(any('installclean' in c or ' clean' in c for c in commands))
        self.assertIn('sepolicy_neverallows', commands[0])
        self.assertIn('adb_root com.android.adbd', commands[0])
        self.assertEqual(commands[-1], 'm -j8 bootimage systemimage')
        self.assertNotIn('/srv/android/asus-build-continuation/scripts/', script)
        self.assertNotIn('SYNTHETIC_FIXTURE', script)

if __name__ == '__main__': unittest.main(verbosity=2)
