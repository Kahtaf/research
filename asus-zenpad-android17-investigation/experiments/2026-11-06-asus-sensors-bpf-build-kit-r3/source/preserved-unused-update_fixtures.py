from pathlib import Path
p=Path(__file__).resolve().parents[1]/'tests/test_kit.py'
s=p.read_text().replace('for n in range(268):\n            p =', 'for n in range(276):\n            p =').replace("'before': baseline[p]", "'before': baseline.get(p)")
s=s.replace("        diff = subprocess.check_output", "        subprocess.run(['git', '-C', str(self.k), 'add', '-N', '.'], check=True)\n        diff = subprocess.check_output")
s=s.replace("        subprocess.run(['git', '-C', str(self.k), 'restore', '.'], check=True)", "        subprocess.run(['git', '-C', str(self.k), 'reset', '-q'], check=True)\n        subprocess.run(['git', '-C', str(self.k), 'restore', '.'], check=True)\n        for n in range(268, 276): (self.k / ('src/' + str(n))).unlink()")
s=s.replace("        put(device / 'device.mk', 'original product\\n')", "        put(device / 'device.mk', 'original product\\n')\n        put(device / 'rootdir/ueventd.rc', 'original ueventd\\n')")
# rootdir change part of the 25 radio changes.
s=s.replace('for n in range(22):', 'for n in range(21):').replace("        put(candidate / 'radio/wificond.rc', 'new wificond')", "        put(candidate / 'radio/wificond.rc', 'new wificond')\n        put(candidate / 'rootdir/ueventd.rc', 'radio ueventd\\n')")
s=s.replace("        input_receipt = jsonput(root / 'inputs/input-mapping.json', input_delta)", """        input_receipt = jsonput(root / 'inputs/input-mapping.json', input_delta)
        previous = jsonput(root / 'inputs/r2-STAGED.json', {'product_after': after})
        previous_inputs = root / 'inputs/r2-product'
        origin = ROOT / 'inputs/sensor-source'
        shutil.copytree(origin, candidate / 'sensors')
        mk = (origin / 'sensors.mk').read_bytes()
        for module in [b'android.hardware.sensors@1.0-service', b'android.hardware.sensors@1.0-impl']:
            mk = mk.replace(module, module + b':64')
        put(candidate / 'sensors/sensors.mk', mk)
        lines = [l for l in (origin / 'ueventd.fragment.rc').read_text().splitlines() if l and not l.startswith('#')]
        suffixes = {'device.mk': i.SENSOR_SUFFIX, 'BoardConfig.mk': b'\\ninclude device/asus/p00a/sensors/BoardConfig.mk\\n', 'rootdir/ueventd.rc': ('\\n' + '\\n'.join(lines) + '\\n').encode()}
        for rel, suffix in suffixes.items():
            put(previous_inputs / rel, (candidate / rel).read_bytes())
            put(candidate / rel, (candidate / rel).read_bytes() + suffix)
        sensor_receipt = jsonput(root / 'inputs/sensor-selection.json', {'original_files': i.manifest(origin), 'files': i.manifest(candidate / 'sensors'), 'suffixes': {p: s.decode() for p,s in suffixes.items()}, 'base_sha256': {p: i.sha(previous_inputs / p) for p in suffixes}, 'after_sha256': {p: i.sha(candidate / p) for p in suffixes}})
        after = i.manifest(candidate)
        prior_changes = {p: dict(v) for p,v in changes.items() if int(p.split('/')[1]) < 268}
        prior_changes['src/267']['after'] = hashlib.sha256(b'r2-267').hexdigest()
        delta = {p: {'before': prior_changes.get(p, {}).get('after'), 'after': changes[p]['after']} for p in ['src/267'] + ['src/' + str(n) for n in range(268, 276)]}
        prior_source = jsonput(root / 'inputs/r2-source.json', {'changes': prior_changes})
        delta_path = jsonput(root / 'inputs/kernel-delta.json', delta)
        platform_paths = {}
        from r3_inputs import PLATFORM
        for name, pin in PLATFORM.items():
            data = (ROOT / 'inputs' / ('bpfloader.rs' if name == 'platform_bpf' else 'PublicVolume.cpp')).read_bytes()
            before_data = (ROOT / 'inputs/bpfloader-before.rs').read_bytes() if name == 'platform_bpf' else data.replace(b'#include <algorithm>\\n', b'', 1)
            active, selected = root / name, staging / name
            put(active / pin['relative'], before_data); put(selected / pin['relative'], data)
            receipt = jsonput(root / 'inputs' / (name + '.json'), {'files': {pin['relative']: {'before': pin['before'], 'after': pin['after']}}, 'patch_sha256': pin['patch']})
            platform_paths.update({name: str(active), name + '_staged': str(selected), name + '_receipt': str(receipt)})
""")
s=s.replace("            'snapshot': receipt_paths['snapshot']}", """            'snapshot': receipt_paths['snapshot'],
            'previous_staged_receipt': str(previous), 'previous_product_inputs': str(previous_inputs),
            'sensor_origin': str(origin), 'sensor_receipt': str(sensor_receipt),
            'previous_source_receipt': str(prior_source), 'kernel_delta': str(delta_path),
            'bpf_supplement_manifest': str(ROOT / 'inputs/bpf-supplement-manifest.json'),
            'bpf_supplement_archive': str(ROOT / 'inputs/bpf-supplement.tar.gz'),
            **platform_paths} """)
s=s.replace("wpa_supplicant P00aWifiBringupOverlay'", "wpa_supplicant P00aWifiBringupOverlay sensors.mt8163 android.hardware.sensors@1.0-service:64 android.hardware.sensors@1.0-impl:64 bpfloader vold'")
p.write_text(s)
