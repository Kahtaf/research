"""Local-only manifest preparation. Does not integrate or start anything."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/srv/android/asus-reviewed-build-kit/r1'
S = '/srv/android/asus-product-integration-staging/r1'
R = '/srv/android/asus-build-continuation'
A = '/srv/android/lineage24'
P = '/srv/android/asus-device-product'
def read(name): return json.loads((ROOT / 'inputs' / name).read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
staged = read('STAGED.json')
source = read('source-receipt.json')
external = {}
for name in ['remote-metadata.json', 'extra-metadata.json']:
    for p, v in json.loads((ROOT / 'evidence' / name).read_text()).items():
        if isinstance(v, dict) and 'sha256' in v: external[p] = v['sha256']
external[S + '/STAGED.json'] = sha(ROOT / 'inputs/STAGED.json')
external[R + '/integration-r5/combined-from-active-soc.patch'] = source['patch_sha256']
external[R + '/integration-r5/combined-source-changes.tar.gz'] = source['source_archive_sha256']
for p, digest in staged['handoff_pins'].items(): external[R + '/integration-r5/' + p] = digest
for p, digest in staged['packaging'].items(): external[S + '/full-boot-tools/' + p] = digest
external[S + '/kernel-config/asus_p00a_combined_defconfig'] = staged['kernel_config_sha256']
external[S + '/product-device/prebuilt/Image.gz-dtb'] = staged['handoff_pins']['Image.gz-dtb']
for name in ['build-source-review.json', 'host-tools-review.json', 'apex-tools-review.json']:
    for rel, item in json.loads((ROOT / 'evidence' / name).read_text()).items():
        external[rel if rel.startswith('/') else A + '/' + rel] = item['sha256']
for rel, digest in read('root-source-pins.json').items(): external[A + '/' + rel] = digest
# The active wificond preimage is checked before integration, not as an immutable
# artifact after integration. Product manifests likewise have explicit phases.
external.pop(A + '/system/connectivity/wificond/wificond.rc', None)
for rel in ['device/asus/p00a/BoardConfig.mk', 'device/asus/p00a/firstboot/firstboot-services.mk']:
    external.pop(A + '/' + rel, None)
plan = {
    'schema': 1, 'run_root': REMOTE, 'revision': 'r6', 'original_pids': [78673, 132874],
    'aosp': A, 'product_out': A + '/out/target/product/p00a', 'logs': P + '/logs',
    'lock': P + '/logs/full-product-build.lock', 'staging': S,
    'kernel': '/srv/android/asus-android17/kernel-bpf-fd', 'kernel_link': A + '/kernel/asus/p00a-fd',
    'compiled_fixture': R + '/kernel', 'device': A + '/device/asus/p00a',
    'connectivity': A + '/packages/modules/Connectivity', 'wificond': A + '/system/connectivity/wificond/wificond.rc',
    'wificond_before': read('product-staging.json')['wificond_before_sha256'],
    'defconfig': '/srv/android/asus-android17/kernel-bpf-fd/arch/arm64/configs/asus_p00a_combined_defconfig',
    'config': S + '/kernel-config/asus_p00a_combined_defconfig',
    'kernel_release': R + '/integration-r5/kernel.release',
    'patch': R + '/integration-r5/combined-from-active-soc.patch',
    'staged_receipt': REMOTE + '/inputs/STAGED.json', 'parity_receipt': REMOTE + '/inputs/firstboot-parent-acceptance.json',
    'source_receipt': REMOTE + '/inputs/source-receipt.json', 'radio_receipt': REMOTE + '/inputs/staged-product-receipt.json',
    'network_receipt': REMOTE + '/inputs/network-staging.json', 'snapshot': REMOTE + '/inputs/snapshot.json',
    'readobj': A + '/prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readobj',
    'clean_receipt': P + '/logs/full-product-installclean.complete', 'external_pins': external,
    'parent_contract': 'PLAN_ONLY default; parent executes after genuine successful r5 terminal. No physical GO.'}
(ROOT / 'inputs/plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
print('Pinned plan, external inputs:', len(external))
