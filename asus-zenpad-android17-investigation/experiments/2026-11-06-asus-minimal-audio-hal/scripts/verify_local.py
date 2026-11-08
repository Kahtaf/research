#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as ET
s=Path(__file__).resolve().parents[1];out=s/'evidence/host';out.mkdir(exist_ok=True)
commands=[['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I'+str(s/'src'),'-I'+str(s/'source/sdk37/external/tinyalsa_new/include'),str(s/'src/transport.c'),str(s/'src/routes.c'),str(s/'tests/transport_test.c'),'-o',str(out/'transport_test')],[str(out/'transport_test')],['xmllint','--noout','--xinclude','--schema',str(s/'source/sdk37/hardware/interfaces/audio/7.1/config/audio_policy_configuration.xsd'),str(s/'staging/config/audio_policy_configuration.xml')]]
receipt=[]
for cmd in commands:
 r=subprocess.run(cmd,capture_output=True,text=True);receipt.append({'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(r.stdout+r.stderr,end='')
 if r.returncode:raise SystemExit(r.returncode)
pins=json.loads((s/'evidence/source-pins.json').read_text())
for p in pins:assert hashlib.sha256((s/p['copy']).read_bytes()).hexdigest()==p['sha256'],p['copy']
policy=ET.parse(s/'staging/config/audio_policy_configuration.xml').getroot()
assert {x.attrib['type'] for x in policy.findall('.//devicePort')}=={'AUDIO_DEVICE_OUT_SPEAKER','AUDIO_DEVICE_IN_BUILTIN_MIC'}
assert all(x.attrib.get('samplingRates')=='48000' for x in policy.findall('.//profile'))
assert all(x.attrib.get('format')=='AUDIO_FORMAT_PCM_16_BIT' for x in policy.findall('.//profile'))
assert 'qualified = false' in (s/'src/routes.c').read_text()
receipt.append({'source_pin_count':len(pins),'source_hash_checks':'PASS','policy_route_profile_consistency':'PASS'})
(s/'evidence/local-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PASS source pins and speaker/mic-only policy contract')
