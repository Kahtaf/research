#!/usr/bin/env python3
"""One bounded local verification: real corrected/bad witnesses and two refusals."""
from pathlib import Path
import json
import struct
from integrity import (ADAPTER_SHA, BAD_SHA, MAPPING, ORIGINAL_SHA, Elf,
                       compare, rename_plan, require, sha)
from stage_importer import rewrite

root = Path(__file__).resolve().parents[1]
workspace = root.parent
old_path = workspace / '2026-11-06-asus-camera-property-map-review/evidence/importer-original.so'
bad_path = workspace / '2026-11-06-asus-camera-property-map/artifacts/arm/libcam_utils.property-map-WITNESS.so'
adapter_path = workspace / '2026-11-06-asus-camera-property-map/artifacts/arm/libasus_camera_legacy_property_map.so'
old, bad, adapter = Elf(old_path), Elf(bad_path), Elf(adapter_path)
require(sha(old.d) == ORIGINAL_SHA and sha(bad.d) == BAD_SHA and sha(adapter.d) == ADAPTER_SHA, 'frozen hash pin')
needed = Elf(root / 'artifacts/importer-needed-only.so')
corrected = Elf(root / 'artifacts/libcam_utils.property-map-CORRECTED-WITNESS.so')
bad_result = compare(old, bad, MAPPING)
good_result = compare(old, corrected, MAPPING)
require(bad_result['status'] == 'FAIL' and bad_result['relocation_mismatch_count'] == 63 and bad_result['symbol_section_mismatch_count'] == 274, 'known bad witness must be caught')
require(good_result['status'] == 'PASS', 'corrected witness failed')
rebuilt, receipt = rewrite(old, needed, adapter)
require(rebuilt == corrected.d, 'local rewrite is not byte reproducible')
require(needed.body(needed.sections['.dynsym']) == corrected.body(corrected.sections['.dynsym']), 'rename changed symbol metadata')
require(needed.body(needed.sections['.gnu.hash']) == corrected.body(corrected.sections['.gnu.hash']), 'rename changed GNU hash')

refusals = []
for case in ('versioned-target', 'reused-string-suffix'):
    data = bytearray(needed.d)
    if case == 'versioned-target':
        struct.pack_into('<H', data, needed.sections['.gnu.version'][4] + 81 * 2, 2)
        expected = 'versioned target import'
    else:
        target = struct.unpack_from('<I', data, needed.sections['.dynsym'][4] + 81 * 16)[0]
        struct.pack_into('<I', data, needed.sections['.dynsym'][4] + 1 * 16, target + len(needed.syms[81][0]) - 3)
        expected = 'reused/conflicting rename range'
    try:
        rename_plan(Elf(bytes(data)))
    except ValueError as error:
        require(expected in str(error), 'refused for an unexpected reason: ' + str(error))
        refusals.append({'case': case, 'status': 'REFUSED', 'reason': str(error), 'output_written': False})
    else:
        raise ValueError('unsafe rename accepted: ' + case)

pins = json.loads((root / 'evidence/original-input-pins.json').read_text())
changed = [name for name, expected in pins.items() if sha((workspace / name).read_bytes()) != expected]
require(not changed, 'original frozen files changed')
(root / 'evidence/known-bad-comparison.json').write_text(json.dumps(bad_result, indent=2) + '\n')
(root / 'evidence/corrected-comparison.json').write_text(json.dumps(good_result, indent=2) + '\n')
summary = {'status': 'PASS static packaging only', 'corrected_sha256': sha(corrected.d),
           'known_bad': {k: bad_result[k] for k in ('status', 'relocation_mismatch_count', 'symbol_section_mismatch_count')},
           'corrected': {k: good_result[k] for k in ('status', 'symbols', 'ordinary_relocations', 'aps2_relocations', 'relocation_mismatch_count', 'symbol_section_mismatch_count', 'ordered_symbol_mismatch_count', 'version_bytes_equal', 'ordered_dependencies_equal')},
           'gnu_hash_lookups': good_result['candidate_layout']['gnu_hash_lookups'],
           'rename_refusals': refusals, 'original_files_checked': len(pins), 'original_files_changed': changed,
           'rewrite_byte_reproducible': True, 'adapter_sha256': sha(adapter.d), 'runtime_executed': False}
(root / 'evidence/verification.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
