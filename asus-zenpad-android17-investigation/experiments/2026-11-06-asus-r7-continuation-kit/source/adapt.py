from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'scripts/integrate.py';s=p.read_text()
s=s.replace('from r3_inputs import','from continuation import terminal, preserve, apply, continuation_inputs\nfrom r3_inputs import')
# Only the r7 continuation module may preserve/apply. Remove obsolete r3 baseline mutation paths.
start=s.index('def terminal(');end=s.index('def revision_unused(',start);s=s[:start]+s[end:]
s=s.replace("plan['revision'] == 'r6'","plan['revision'] == 'r7'")
start=s.index('def destinations(');end=s.index('def verify_integrated(',start);s=s[:start]+s[end:]
start=s.index('def apply(');end=s.index('def execute(',start);s=s[:start]+s[end:]
s=s.replace("need(manifest(plan['device']) == s['product_before'], 'Active device preimage mismatch')","continuation_inputs(plan)\n    need(manifest(plan['device']) == read(plan['prior_staged_receipt'])['product_after'], 'Already-integrated r3 device preimage mismatch')")
s=s.replace('platforms = platform_selection(plan)','platforms = platform_selection(plan, phase=\'after\')')
s=s.replace("net['connectivity_before'].items()","net['connectivity_after'].items()")
s=s.replace("{'sha256': plan['wificond_before']}","s['product_after']['radio/wificond.rc']")
s=s.replace("need(not Path(plan['defconfig']).exists(), 'Combined defconfig already present')","need(sha(plan['defconfig']) == s['kernel_config_sha256'], 'Already-integrated config drift')")
s=s.replace("expected = {'sha256': change['before']} if change['before'] else None","expected = {'sha256': change['after']}")
s=s.replace("selected == set(snapshot['files'])","selected == set(snapshot['files']) | set(source['changes']) | {str(Path(plan['defconfig']).relative_to(plan['kernel']))}")
s=s.replace("{'sha256': digest}, 'Baseline mismatch: '","{'sha256': source['changes'].get(rel, {}).get('after', digest)}, 'Integrated baseline mismatch: '")
s=s.replace("        subprocess.run(['git', '-C', plan['kernel'], 'apply', '--check', '--whitespace=nowarn', plan['patch']], check=True)\n",'')
s=s.replace("preserve(plan, attempt)","preserve(plan, attempt, previous)")
s=s.replace("            apply(plan, attempt)","            terminal(plan, review)\n            apply(plan, attempt)")
s=s.replace("'.reviewed-r6-tmp'","'.reviewed-r7-tmp'")
s=s.replace("'Parent-executed, one-shot integration.","'Parent-executed, one-shot continuation.")
s=s.replace("    platforms = platform_selection(plan, phase='after')\n    sensor_selection(plan, s)","    continuation_inputs(plan)\n    need(Path(plan['kernel_link']).resolve() == Path(plan['kernel']), 'Kernel source link drift')\n    snapshot = read(plan['snapshot'])\n    need(subprocess.check_output(['git','-C',plan['kernel'],'rev-parse','HEAD'],text=True).strip() == snapshot['head'] == source['base_commit'], 'Kernel base HEAD drift')\n    platforms = platform_selection(plan, phase='after')\n    sensor_selection(plan, s)")
p.write_text(s)
p=R/'scripts/r3_inputs.py';s=p.read_text();s=s.replace(" expected['sensors.mk']={'sha256':hashlib.sha256(mk).hexdigest()}"," expected['sensors.mk']={'sha256':hashlib.sha256(mk).hexdigest()}\n from continuation import sensor_delta\n delta=sensor_delta(plan)\n expected['BoardConfig.mk']={'sha256':delta['after']}")
p.write_text(s)
p=R/'scripts/build.sh';s=p.read_text().replace('/r3 ]]','/r7 ]]').replace('full-build-r6','full-build-r7');s=s.replace("SELINUX_IGNORE_NEVERALLOWS' >", "SELINUX_IGNORE_NEVERALLOWS BOARD_SEPOLICY_DIRS BOARD_VENDOR_SEPOLICY_DIRS BOARD_ODM_SEPOLICY_DIRS SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS PRODUCT_PUBLIC_SEPOLICY_DIRS PRODUCT_PRIVATE_SEPOLICY_DIRS BOARD_PLAT_PUBLIC_SEPOLICY_DIR BOARD_PLAT_PRIVATE_SEPOLICY_DIR BOARD_REQD_MASK_POLICY BOARD_SYSTEM_EXT_PREBUILT_DIR BOARD_PRODUCT_PREBUILT_DIR BOARD_VENDOR_SEPOLICY_PREBUILT_DIR BOARD_ODM_SEPOLICY_PREBUILT_DIR DEVICE_MANIFEST_FILE' >")
s=s.replace('python3 -B "$kit/scripts/verify_full_images.py" vars "$record.vars"','python3 -B "$kit/scripts/verify_full_images.py" vars "$record.vars"\npython3 -B "$kit/scripts/verify_config_paths.py" "$record.vars" "$kit" "$kit/attempt/product-config-paths.json"')
p.write_text(s)
p=R/'scripts/verify_product_r3.py';s=p.read_text().replace('r6','r7');p.write_text(s)
p=R/'scripts/validate_completed_product.py';s=p.read_text().replace("'r3-product-provenance.json'","'r7-product-provenance.json'").replace("'r3_product_provenance_sha256'","'r7_product_provenance_sha256'");s=s.replace("    values = variables(Path(str(record) + '.vars'))","    from verify_config_paths import verify as verify_paths\n    config_paths = verify_paths(Path(str(record) + '.vars'), plan)\n    need(read(root / 'attempt/product-config-paths.json') == config_paths, 'Product configuration receipt drift')\n    values = variables(Path(str(record) + '.vars'))")
s=s.replace("'parent_parity_sha256':", "'product_config_paths_sha256': sha(root / 'attempt/product-config-paths.json'),\n          'sensor_delta_sha256': sha(plan['sensor_delta']), 'prior_integration_sha256': sha(plan['prior_integration']),\n          'parent_parity_sha256':")
p.write_text(s)
