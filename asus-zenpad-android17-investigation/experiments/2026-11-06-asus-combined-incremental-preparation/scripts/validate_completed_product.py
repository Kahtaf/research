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
    from admission import require_binding
    require_binding(Path('/srv/android/asus-combined-incremental-prep-r1'))
    need(__debug__, 'Optimized Python forbidden')
    seal = verify_pins(root)
    plan = read(Path('/srv/android/asus-combined-incremental-prep-r1/inputs/plan.json'))
    a = Path(plan['aosp'])
    p = Path(plan['product_out'])
    b = a / 'out/host/linux-x86/bin'
    record = Path('/srv/android/asus-combined-incremental-prep-r1/logs/full-build-combined-r1')
    o = Path(os.environ['VALIDATION_DIR'])
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

    from verify_config_paths import verify as verify_paths
    config_paths = verify_paths(Path(str(record) + '.vars'), plan)
    need(read('/srv/android/asus-combined-incremental-prep-r1/inputs/expected-config-paths.json') == config_paths, 'Exact root-enabled configuration receipt drift')
    values = variables(Path(str(record) + '.vars'))
    need(values.get('SELINUX_IGNORE_NEVERALLOWS', '') in ('', 'false'), 'Neverallow checks disabled')
    report = read(Path(str(record) + '.images.json'))
    integration = read(root / 'attempt/integration.json')
    from continuation import R8_SEAL, continuation_inputs
    from artifact import REL, BEFORE, OID, admit
    continuation_inputs(plan)
    need(integration.get('revision') == 'r9' and integration.get('prior_kit_pins_sha256') == R8_SEAL and integration.get('prior_integration_receipt_sha256') == sha(plan['r8_integration']) and integration.get('r9_delta_sha256') == sha(plan['r9_delta']), 'r9 integration lineage mismatch')
    need(integration['source_writes'] == [dict(path=str(Path(plan['aosp']) / REL), before=BEFORE, after=OID)], 'r9 source-write receipt differs from exact artifact materialization')
    admit(Path(plan['aosp']) / REL)
    staged = read(plan['staged_receipt'])
    need(manifest(plan['device']) == read('/srv/android/asus-combined-incremental-prep-r1/inputs/expected-product.json'), 'Exact root-enabled product manifest drift')
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
    libs['liblog.so'] = p / 'system/lib/liblog.so'  # Actual SDK37 installed ARM32 LLNDK provider.
    for name, path in libs.items():
        need(path.is_file() and path.read_bytes()[:5] == b'\x7fELF\x01', 'Missing/wrong final ARM32 ELF: ' + str(path))
    deps = {'libbtcal.so': ['libc++.so', 'libc.so', 'libdl.so', 'libm.so'],
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
    from verify_zram_context import verify as verify_zram
    write(o / 'zram-context.json', verify_zram(partition, policy, b / 'sefcontext_compile', o / 'zram-context'))
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
    reservation = Path('/srv/android/asus-combined-incremental-prep-r1/attempt/raw-reservation.json')
    if reservation.exists():
        need(reservation.with_name('raw-materialized.json').is_file(), 'Incomplete raw reservation; do not rematerialize')
        reuse = read(reservation.with_name('raw-materialized.json'))
        need(reuse['source_system_sha256'] == report['system']['sha256'], 'Raw reservation binds another native image')
        raw = Path(reuse['path'])
        need(raw.is_file() and raw.stat().st_size == 3753902080 and reuse.get('sha256') == sha(raw), 'Previous materialization incomplete or changed; preserve it, do not duplicate')
    else:
        raw = o / 'system-partition.raw'
        write(reservation, {'source_system_sha256': report['system']['sha256'], 'path': str(raw), 'state': 'RESERVED_BEFORE_WRITE'})
        expanded = o / 'expanded-system.tmp'
        if sparse:
            run([b / 'simg2img', image, expanded])
            need(expanded.stat().st_size == report['system']['expanded_bytes'], 'Wrong expanded SYSTEM size')
        raw = o / 'system-partition.raw'
        materialize(expanded if sparse else image, raw, 3753902080)
        if sparse:
            expanded.unlink()  # Disposable conversion only; original images/logs preserved.
        # Preserve reservation history and publish the verified materialization separately.
        write(reservation.with_name('raw-materialized.json'), {'source_system_sha256': report['system']['sha256'], 'path': str(raw), 'sha256': sha(raw), 'state': 'COMPLETE'})
    run([b / 'e2fsck', '-f', '-n', raw])
    from verify_product_r3 import installed
    write(o / 'zram-context-system-bytes.json', installed(p, 'system/vendor/etc/selinux/vendor_file_contexts', raw, b / 'debugfs', sha(partition['vendor'] / 'etc/selinux/vendor_file_contexts')))
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
    write(o / 'r8-product-provenance.json', verify_r3(plan, root, raw, b / 'debugfs', readelf, apex))
    root_check = verify_root(p, apex, read(root / 'inputs/root-source-pins.json')['packages/modules/adb/root/adb_root.rc'], raw, b / 'debugfs')
    write(o / 'root-payload.json', root_check)
    # Genuine compatibility evaluation uses the unchanged kernel's embedded IKCONFIG.
    tools = Path(plan['staging']) / 'full-boot-tools/scripts'
    sys.path.insert(0, str(tools))
    import package_full_boot as packager
    source_kernel = packager.components((p / 'boot.img').read_bytes())[1]
    embedded = packager.kernel_config(packager.ungzip(source_kernel)[0])
    need(__import__('hashlib').sha256(embedded).hexdigest() == '10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2', 'Actual embedded kernel config changed')
    exact_config = o / 'embedded-kernel.config'
    with exact_config.open('xb') as stream: stream.write(embedded)
    command = [b / 'checkvintf', '--check-compat']
    for label, path in dirmap.items(): command += ['--dirmap', label + ':' + str(path)]
    command += ['--kernel', str(release) + ':' + str(exact_config), '--property', 'ro.product.first_api_level=23',
                '--property', 'ro.boot.product.hardware.sku=', '--property', 'ro.boot.product.vendor.sku=']
    vintf_log = o / 'checkvintf.log'
    with vintf_log.open('xb') as stream:
        vintf_result = subprocess.run(list(map(str, command)), stdout=stream, stderr=subprocess.STDOUT)
    write(o / 'vintf-result.json', {'argv': list(map(str, command)), 'exit': vintf_result.returncode,
          'tool_sha256': sha(b / 'checkvintf'), 'embedded_config_sha256': sha(exact_config),
          'log': str(vintf_log), 'log_sha256': sha(vintf_log), 'requirements_removed': False})
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
    from admission import require_binding
    bound = require_binding(Path('/srv/android/asus-combined-incremental-prep-r1'))
    checker = bound['proof']['final_checker']
    args = [value.format(product=str(p), raw=str(raw), apex=str(apex)) for value in checker['argv']]
    need(sha(args[0]) == checker['tool_sha256'], 'Final namespace checker identity changed')
    run(args)
    write(o / 'complete.json', {'kit_pins_sha256': seal, 'integration_receipt_sha256': sha(root / 'attempt/integration.json'),
          'product_config_paths_sha256': sha(root / 'attempt/product-config-paths.json'),
          'native_lineage_map_sha256': sha(plan['native_lineage_map']), 'bpf_classification_sha256': sha(plan['qualified_baseline_map']),
          'parent_native_cache_method_sha256': sha(plan['native_cache_method']), 'parent_bpf_conditional_method_sha256': sha(plan['bpf_runtime_conditional_method']),
          'changed_bpf_runtime_requalification_required': True, 'bpf_host_checks_scope': 'ELF/compiler/graph/final installed bytes; runtime acceptance conditional',
          'r9_delta_sha256': sha(plan['r9_delta']), 'r8_delta_sha256': sha(plan['r8_delta']), 'sensor_delta_sha256': sha(plan['sensor_delta']), 'prior_integration_sha256': sha(plan['r7_integration']),
          'parent_parity_sha256': sha(plan['parity_receipt']), 'source_patch_sha256': sha(plan['patch']),
          'source_receipt_sha256': sha(plan['source_receipt']), 'active_source_postimages_sha256': sha(o / 'source-postimages.json'), 'staged_receipt_sha256': sha(plan['staged_receipt']),
          'raw_system': {'path': str(raw), 'bytes': raw.stat().st_size, 'sha256': sha(raw), 'all_zero_ranges_written': True, 'writer_must_materialize_all_zero_ranges': True},
          'boot': {'path': str(boot), 'sha256': sha(boot), 'source_aosp_sha256': report['boot']['sha256']},
          'source_system_sha256': report['system']['sha256'], 'google_signed_metadata_files': len(google['checked']), 'root_payload_receipt_sha256': sha(o / 'root-payload.json'),
          'input_mapping_payload_sha256': sha(o / 'input-mapping-payload.json'),
          'zram_context_sha256': sha(o / 'zram-context.json'), 'zram_context_system_bytes_sha256': sha(o / 'zram-context-system-bytes.json'),
          'r8_product_provenance_sha256': sha(o / 'r8-product-provenance.json'),
          'google_unsigned_outputs_sha256': sha(o / 'google-unsigned-outputs.json'), 'google_total_payloads_checked': 32,
          'kernel_sha256': sha(kernel), 'config_sha256': sha(config), 'host_tool_hashes': tool_pins,
          'elf_init_policy_neverallows_apex_host_checks_passed': True,
          'root_route_accepted': True, 'compatibility_incomplete': False, 'vintf_compatible': vintf_result.returncode == 0, 'overall_validation_passed': vintf_result.returncode == 0,
          'full_service_chain_accepted': False, 'root_runtime_verified': False,
          'physical_boot_verified': False, 'flash_ready': False})

    need(vintf_result.returncode == 0, 'Actual VINTF compatibility failed; retain HAL/kernel errors and independently packaged artifacts')

if __name__ == '__main__':
    validate(Path(sys.argv[1]).resolve())
