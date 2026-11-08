#!/usr/bin/env python3
"""Host qualification of real completed outputs; never publishes flash readiness."""
import json
import os
from pathlib import Path
import subprocess
import sys
from integrate import need, sha, read, write, verify_pins, manifest, verify_integrated
from verify_google_payload import verify as verify_google
from verify_root_payload import verify as verify_root, verify_ramdisk_properties
from verify_full_images import variables, inspect_system
from verify_input_payload import verify as verify_input
from verify_product_r3 import verify as verify_r3
from verify_google_transformed import verify as verify_google_transformed


def materialize(source, destination, size):
    """Write every byte, including zero ranges and the partition tail (no seeks)."""
    need(source.stat().st_size <= size, 'SYSTEM exceeds partition')
    with source.open('rb') as src, destination.open('xb') as dst:
        total = 0
        for block in iter(lambda: src.read(1024 * 1024), b''):
            dst.write(block)
            total += len(block)
        zero = bytes(1024 * 1024)
        while total < size:
            block = zero[:min(len(zero), size - total)]
            dst.write(block)
            total += len(block)
        dst.flush()
        os.fsync(dst.fileno())
    need(destination.stat().st_size == size, 'Wrong raw SYSTEM length')


def verify_source_images(product, report):
    for name in ('boot', 'system'):
        need(sha(product / (name + '.img')) == report[name]['sha256'], 'Source image changed: ' + name)


def validate(root):
    need(__debug__, 'Optimized Python forbidden')
    seal = verify_pins(root)
    plan = read(root / 'inputs/plan.json')
    a = Path(plan['aosp'])
    p = Path(plan['product_out'])
    b = a / 'out/host/linux-x86/bin'
    record = Path(plan['logs']) / ('full-build-' + plan['revision'])
    o = root / 'attempt/validation'
    o.mkdir()
    records = []
    tool_pins = {}

    def run(args):
        args = list(map(str, args))
        exe = Path(args[0])
        if exe.is_file():
            tool_pins[str(exe)] = sha(exe)
        log = o / ('command-' + str(len(records)) + '.log')
        with log.open('xb') as f:
            result = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
        records.append({'argv': args, 'exit': result.returncode, 'log': str(log), 'sha256': sha(log)})
        # Each incremental journal is exclusive and preserved, including failure.
        write(o / ('commands-' + str(len(records)) + '.json'), records)
        need(result.returncode == 0, 'Host check failed: ' + str(log))

    values = variables(Path(str(record) + '.vars'))
    need(values.get('SELINUX_IGNORE_NEVERALLOWS', '') in ('', 'false'), 'Neverallow checks disabled')
    report = read(Path(str(record) + '.images.json'))
    integration = read(root / 'attempt/integration.json')
    staged = read(plan['staged_receipt'])
    need(manifest(plan['device']) == staged['product_after'], 'Integrated product drift')
    for path, expected in plan['external_pins'].items():
        # These are immutable reviewed candidates, receipts and source tools.
        need(sha(path) == expected, 'Reviewed external input changed: ' + path)
    config = Path(integration['generated_defconfig']['path'])
    release = Path(integration['kernel_release']['path'])
    need(sha(config) == integration['generated_defconfig']['sha256'], 'Config drift')
    need(sha(release) == integration['kernel_release']['sha256'], 'Release drift')
    verify_source_images(p, report)
    need(report['system'] == inspect_system(p / 'system.img', 3753902080), 'Source SYSTEM report drift')
    # Validate installed init across partitions with actual generated passwd/context data.
    partition = {'system': p / 'system', 'vendor': p / 'system/vendor',
                 'product': p / 'system/product', 'system_ext': p / 'system/system_ext'}
    command = [b / 'host_init_verifier']
    for label, path in partition.items():
        need(path.is_dir(), 'Missing installed partition ' + label)
        command += ['--out_' + label + '=' + str(path)]
        passwd = path / 'etc/passwd'
        if passwd.is_file():
            command += ['-p', passwd]
        contexts = path / 'etc/selinux' / (('plat' if label == 'system' else label) + '_property_contexts')
        if contexts.is_file():
            command += ['--property-contexts=' + str(contexts)]
    run(command)
    # Strict real ARM32 link checks against the final installed dependencies.
    shared = p / 'system/vendor/lib'
    libs = {n: shared / n for n in ['libbtcal.so', 'libbluetooth_mtk.so', 'libbt-vendor.so', 'libc++.so', 'libcutils.so', 'liblog.so']}
    libs.update({n: p / 'system/lib/bootstrap' / n for n in ['libc.so', 'libdl.so', 'libm.so']})
    for name, path in libs.items():
        need(path.is_file() and path.read_bytes()[:5] == b'\x7fELF\x01', 'Missing/wrong final ARM32 ELF: ' + str(path))
    deps = {'libbtcal.so': ['libc.so'],
            'libbluetooth_mtk.so': ['liblog.so', 'libcutils.so', 'libbtcal.so', 'libc++.so', 'libdl.so', 'libc.so', 'libm.so'],
            'libbt-vendor.so': ['liblog.so', 'libbluetooth_mtk.so', 'libc++.so', 'libdl.so', 'libc.so', 'libm.so']}
    for name, needed in deps.items():
        command = [sys.executable, a / 'build/make/tools/check_elf_file.py', '--llvm-readobj', plan['readobj'], '--soname', name, '--max-page-size', '4096']
        for dependency in needed:
            command += ['--shared-lib', libs[dependency]]
        run(command + [libs[name]])
    # Build already requested SDK37 sepolicy_neverallows; independently link installed
    # CIL with neverallow enabled, then check installed file and property contexts.
    version = (partition['vendor'] / 'etc/selinux/plat_sepolicy_vers.txt').read_text().strip()
    need(version.replace('.', '').isdigit(), 'Invalid real vendor policy version')
    cil = [partition['system'] / 'etc/selinux/plat_sepolicy.cil',
           partition['system_ext'] / 'etc/selinux/system_ext_sepolicy.cil',
           partition['product'] / 'etc/selinux/product_sepolicy.cil',
           partition['vendor'] / 'etc/selinux/plat_pub_versioned.cil',
           partition['system'] / ('etc/selinux/mapping/' + version + '.cil'),
           partition['vendor'] / 'etc/selinux/vendor_sepolicy.cil']
    for label in ('system_ext', 'product'):
        mapping = partition[label] / ('etc/selinux/mapping/' + version + '.cil')
        if mapping.is_file(): cil.append(mapping)
    need(all(f.is_file() for f in cil), 'Missing installed CIL inputs')
    policy = o / 'policy.bin'
    run([b / 'secilc', '-m', '-M', 'true', '-G', '-c', '30', *cil, '-o', policy, '-f', o / 'generated-contexts'])
    properties = []
    for label, path in partition.items():
        prefix = 'plat' if label == 'system' else label
        # Android permits an empty product-specific context supplement. Platform
        # and vendor contexts remain mandatory, with full CIL neverallow checks.
        flags = ['-e'] if label == 'product' else []
        run([b / 'checkfc', *flags, policy, path / ('etc/selinux/' + prefix + '_file_contexts')])
        properties.append(path / ('etc/selinux/' + prefix + '_property_contexts'))
    run([b / 'property_info_checker', policy, *properties])
    image = p / 'system.img'
    with image.open('rb') as f:
        sparse = f.read(4) == bytes.fromhex('3aff26ed')
    expanded = o / 'expanded-system.tmp'
    if sparse:
        run([b / 'simg2img', image, expanded])
        need(expanded.stat().st_size == report['system']['expanded_bytes'], 'Wrong expanded SYSTEM size')
    raw = o / 'system-partition.raw'
    materialize(expanded if sparse else image, raw, 3753902080)
    if sparse:
        expanded.unlink()  # Disposable conversion only; original images/logs preserved.
    run([b / 'e2fsck', '-f', '-n', raw])
    google = verify_google(read(root / 'inputs/google-inline-source-manifest.json'), p, raw, b / 'debugfs')
    need(len(google['checked']) == 30 and len(google['unsigned_build_transformed_inputs']) == 2, 'Google payload coverage incomplete')
    write(o / 'google-signed-bytes.json', google)
    readelf = Path(plan['readobj']).with_name('llvm-readelf')
    write(o / 'google-unsigned-outputs.json', verify_google_transformed(read(root / 'inputs/google-inline-source-manifest.json'), p, raw, b / 'debugfs', readelf, a))
    write(o / 'input-mapping-payload.json', verify_input(p, raw, b / 'debugfs'))
    apex = o / 'apex'
    apex.mkdir()
    odm = partition['vendor'] / 'odm'
    if not odm.exists():
        odm = o / 'empty-odm'
        odm.mkdir()
    dirmap = {**{'/' + label: path for label, path in partition.items()}, '/odm': odm, '/apex': apex}
    command = [b / 'apexd_host', '--tool_path', a / 'out/host/linux-x86', '--apex_path', apex]
    for label, path in dirmap.items():
        if label != '/apex': command += ['--' + label[1:] + '_path', path]
    run(command)
    need((apex / 'apex-info-list.xml').is_file(), 'No real extracted APEX metadata')
    write(o / 'r3-product-provenance.json', verify_r3(plan, root, raw, b / 'debugfs', readelf, apex))
    root_check = verify_root(p, apex, read(root / 'inputs/root-source-pins.json')['packages/modules/adb/root/adb_root.rc'], raw, b / 'debugfs')
    write(o / 'root-payload.json', root_check)
    command = [b / 'checkvintf', '--check-compat']
    for label, path in dirmap.items():
        command += ['--dirmap', label + ':' + str(path)]
    command += ['--kernel', str(release) + ':' + str(config), '--property', 'ro.product.first_api_level=23',
                '--property', 'ro.boot.product.hardware.sku=', '--property', 'ro.boot.product.vendor.sku=']
    run(command)
    # Only actual completed BOOT is accepted, never a synthetic CLI mode/fixture.
    tools = Path(plan['staging']) / 'full-boot-tools/scripts'
    sys.path.insert(0, str(tools))
    import package_full_boot as packager
    kernel = Path(plan['staging']) / 'product-device/prebuilt/Image.gz-dtb'
    packed, dtb, packaging = packager.package((p / 'boot.img').read_bytes(), kernel.read_bytes(), report, synthetic=False)
    actual_ramdisk = packager.components((p / 'boot.img').read_bytes())[2]
    actual_entries = packager.parse_cpio(packager.ungzip(actual_ramdisk)[0])
    packaging['actual_ramdisk_property_hashes'] = verify_ramdisk_properties(actual_entries, p)
    need(packaging['compiled_config_sha256'] == sha(config), 'Packaged embedded config mismatch')
    need(packaging['header_cmdline_bytes'] == 92 and packaging['ramdisk']['synthetic_nonbootable'] is False, 'Wrong full BOOT contract')
    boot = o / 'UNTESTED-sdk37-combined-boot.img'
    with boot.open('xb') as f: f.write(packed)
    with (o / 'packaged.dtb').open('xb') as f: f.write(dtb)
    write(o / 'packaging.json', packaging)
    verify_source_images(p, report)
    write(o / 'source-postimages.json', verify_integrated(plan, baseline=True))
    need(sha(boot) == packaging['image_sha256'], 'Final BOOT write mismatch')
    raw.chmod(0o444)
    write(o / 'complete.json', {'kit_pins_sha256': seal, 'integration_receipt_sha256': sha(root / 'attempt/integration.json'),
          'parent_parity_sha256': sha(plan['parity_receipt']), 'source_patch_sha256': sha(plan['patch']),
          'source_receipt_sha256': sha(plan['source_receipt']), 'active_source_postimages_sha256': sha(o / 'source-postimages.json'), 'staged_receipt_sha256': sha(plan['staged_receipt']),
          'raw_system': {'path': str(raw), 'bytes': raw.stat().st_size, 'sha256': sha(raw), 'all_zero_ranges_written': True, 'writer_must_materialize_all_zero_ranges': True},
          'boot': {'path': str(boot), 'sha256': sha(boot), 'source_aosp_sha256': report['boot']['sha256']},
          'source_system_sha256': report['system']['sha256'], 'google_signed_metadata_files': len(google['checked']), 'root_payload_receipt_sha256': sha(o / 'root-payload.json'),
          'input_mapping_payload_sha256': sha(o / 'input-mapping-payload.json'),
          'r3_product_provenance_sha256': sha(o / 'r3-product-provenance.json'),
          'google_unsigned_outputs_sha256': sha(o / 'google-unsigned-outputs.json'), 'google_total_payloads_checked': 32,
          'kernel_sha256': sha(kernel), 'config_sha256': sha(config), 'host_tool_hashes': tool_pins,
          'elf_init_policy_neverallows_vintf_apex_host_checks_passed': True,
          'full_service_chain_accepted': False, 'root_runtime_verified': False,
          'physical_boot_verified': False, 'flash_ready': False})

if __name__ == '__main__':
    validate(Path(sys.argv[1]).resolve())
