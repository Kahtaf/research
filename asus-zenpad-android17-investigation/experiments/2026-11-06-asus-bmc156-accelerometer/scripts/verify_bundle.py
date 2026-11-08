#!/usr/bin/env python3
"""Offline bundle verification: no SSH, devices, active-source writes or builds."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
S=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=0
def check(condition):
 global checks
 assert condition
 checks+=1
manifest=json.loads((S/'bundle-manifest.json').read_text())
for rel,h in manifest.items():check(sha(S/rel)==h)
R=S/'artifacts/remote';m=json.loads((R/'export-manifest.json').read_text())
for rel,h in m.items():check(sha(R/rel)==h)
v=json.loads((R/'evidence/final-verification.json').read_text());patch=json.loads((S/'patches/pre-post-hashes.json').read_text())
check(v['source_changes']==patch);check(len(patch)==9)
for rel,row in patch.items():
 check(sha(S/'source/kernel'/rel)==row['after'])
 p=S/'source/kernel-preimages'/rel
 check((sha(p) if p.is_file() else None)==row['before'])
check(sha(R/'artifacts/sensors.mt8163.so')==v['hal_sha256'])
check(sha(R/'evidence/resolved.config')==v['resolved_config_sha256'])
check(v['original_physical_source_unchanged'] and v['charging_opt_in_absent'])
check(v['protected_runtime_source_count']==282 and v['protected_runtime_config_count']==58)
check(not v['full_image_built'] and not v['physical_hardware_tested'] and not v['device_operations'])
for name in ['kernel-math-test.json','protocol-test.json','hal-callback-tests.json','registration-test.json','core-state-test.json']:
 check(json.loads((R/'evidence'/name).read_text())['exit']==0)
check(all(x['exit']==0 for x in json.loads((R/'evidence/policy-merge.json').read_text())))
check(json.loads((R/'evidence/vintf-schema.json').read_text())['exit']==0)
check(json.loads((S/'evidence/patch-roundtrip.json').read_text())['patch_sha256']==sha(S/'patches/kernel-from-physical-r5.patch'))
check(json.loads((S/'evidence/oem-patch-roundtrip.json').read_text())['patch_sha256']==sha(S/'patches/oem-driver-adaptation.patch'))
xml=ET.parse(S/'source/hal/manifest.xml').getroot();check(len(xml.findall('hal'))==1 and xml.findtext('hal/name')=='android.hardware.sensors' and xml.findtext('hal/version')=='1.0')
check(json.loads((S/'evidence/r5-source-chain.json').read_text())['exact_parent_compiled_r5_source_match'])
print(f'PASS {checks} offline artifact/ABI/preservation checks; hardware remains unproved')
