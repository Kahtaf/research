#!/usr/bin/env python3
"""Replay pinned LK semantic rules against the corrected artifact; no target I/O."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
path = ROOT / 'source/model_reference.py'
expected = '73d6074c84110aa7328174fcc19561d4ddd368abd3f96414265374387d1c822c'
assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
spec = importlib.util.spec_from_file_location('pinned_lk_reference', path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
name = '2026-11-06-asus-linux49-probe-initrd-fix/artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img'
image_sha = '45551fec6af489bef6813131fb3854eddcfe95d3ca3fa640fea7a37dfd21b630'
result, loaded, moved = model.inspect(name, image_sha)
effective = result['effective_initrd_with_no_extra_runtime_initrd_token']
assert effective['agrees_with_moved_payload'] and effective['gzip_magic_at_effective_start']
assert effective['offset_into_moved_stream'] == 0
assert not result['cmdline']['header_truncated'] and result['cmdline']['header_bytes'] == 95
assert moved[:2] == b'\x1f\x8b'
(ROOT / 'evidence/r3-handoff-model.json').write_text(json.dumps(result, indent=2) + '\n')
receipt = {'status': 'R3_STATIC_HANDOFF_CORRECTION_VERIFIED', 'image_sha256': image_sha,
           'reference_model_sha256': expected, 'old_reference_boundary_checks': 14,
           'effective_initrd': effective, 'header_cmdline_bytes': 95, 'device_operations': 0,
           'physical_boot_proven': False, 'transport_profile_ready': False}
(ROOT / 'evidence/parent-correction-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
gate = {'obsolete_r2_sha256': '48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48',
        'r2_install_authorized': False,
        'reason': 'Exact LK moves compressed ramdisk to44000000; R2 explicitinitrd skipped512bytes',
        'corrected_r3': receipt, 'full_boot_packager_requires_same_correction': True,
        'full_boot_lk_header_limit_must_be_enforced': 99,
        'stock_rescue_old_dt_2MiB_clamp_hypothesis': 'Refuted by exact LK bootargs replacement; final armed image still needs fit/layout review'}
(WORK / '2026-11-06-asus-android17-orchestration/evidence/probe-r2-invalid-r3-correction.json').write_text(json.dumps(gate, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
