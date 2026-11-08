#!/usr/bin/env python3
"""Offline checks only. Does not SSH, build a kernel, or access Android devices."""
import hashlib, json, pathlib, re, subprocess, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEVICE=ROOT/'staged/device/asus/p00a/connectivity'
QA=ROOT/'evidence/qa';QA.mkdir(parents=True,exist_ok=True)
checks=[]
def run(label, command, expected=0, cwd=ROOT):
 p=subprocess.run(command,cwd=cwd,text=True,capture_output=True)
 (QA/(label+'.txt')).write_text(p.stdout+p.stderr)
 checks.append({'check':label,'passed':p.returncode==expected,'returncode':p.returncode,'expected':expected})
 if p.returncode != expected:
  raise RuntimeError(label+': '+p.stdout+p.stderr)
def check(label, condition):
 checks.append({'check':label,'passed':bool(condition)})
 if not condition:raise RuntimeError(label)
try:
 for name in ['stock-input-manifest.json','remote-files.json','local-source-manifest.json']:
  m=json.loads((ROOT/'evidence'/name).read_text())
  rows=m if isinstance(m,list) else m.values()
  for row in rows:
   p=ROOT/row.get('staged',row.get('local'))
   check('sha256:'+str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'])
 for p in (ROOT/'staged').rglob('*'):
  if p.name.endswith(('.xml','.xml.template')):ET.parse(p)
 check('all-staged-xml-parses',True)
 run('gpl-firmware-patch-dry-run',['git','apply','--check',str(ROOT/'staged/patches/0001-asus-gpl-use-vendor-firmware.patch')],cwd=ROOT/'sources/asus-gpl/kernel-3.18')
 run('gpl-bt-compat-patch-dry-run',['git','apply','--check',str(ROOT/'staged/patches/0002-asus-gpl-bt-compat-ioctl-width.patch')],cwd=ROOT/'sources/asus-gpl/kernel-3.18')
 run('host-preflight-compile',['cc','-std=c11','-Wall','-Wextra','-Werror',str(DEVICE/'src/connectivity_check.c'),'-o',str(QA/'connectivity-check-host')])
 run('host-preflight-missing-driver-fails',[str(QA/'connectivity-check-host')],expected=2)
 run('host-adapter-compile',['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(ROOT/'tests/include'),str(ROOT/'tests/driver_cmd_behavior.c'),'-o',str(QA/'driver-cmd-test')])
 run('host-adapter-behavior',[str(QA/'driver-cmd-test')])
 source=(DEVICE/'src/driver_cmd_p00a.c').read_text()
 header=(ROOT/'sources/lineage24/external/wpa_supplicant_8/src/drivers/driver_nl80211.h').read_text()
 exported=['wpa_driver_nl80211_driver_cmd','wpa_driver_set_p2p_noa','wpa_driver_get_p2p_noa','wpa_driver_set_p2p_ps','wpa_driver_set_ap_wps_p2p_ie']
 for symbol in exported:
  pattern=r'(?:extern\s+)?int\s+'+symbol+r'\s*\((.*?)\)'
  normalize=lambda s:re.sub(r'\s+','',s)
  a=re.search(pattern,source,re.S); b=re.search(pattern,header,re.S)
  check('current-supplicant-declaration:'+symbol,bool(a and b and normalize(a[1])==normalize(b[1])))
 check('no-private-ioctl-forwarding','SIOCDEVPRIVATE' not in source)
 check('base-does-not-enable-radios',all(s not in (DEVICE/'connectivity-base.mk').read_text() for s in ['wpa_supplicant','service.p00a','libbt-vendor']))
 for p in DEVICE.rglob('*.mk'):
  for match in re.finditer(r'(?:\$\(P00A_CONNECTIVITY_PATH\)|device/asus/p00a/connectivity)/([^\s:]+):',p.read_text()):
   check('product-copy-source:'+match[1],(DEVICE/match[1]).is_file())
 gate=json.loads((ROOT/'evidence/kernel-gate.json').read_text())
 check('current-kernel-correctly-reported-blocked',not gate['transport_gate_passed'] and not any(gate['linked_required_symbols'].values()))
 check('no-calibration-records-staged',not any(p.name in ['WIFI','WIFI_CUSTOM','BT_Addr','BT'] for p in (ROOT/'staged').rglob('*') if p.is_file()))
finally:
 (ROOT/'evidence/validation.json').write_text(json.dumps({'scope':'Offline host/source/artifact checks only; no Android target or kernel build, no hardware validation','checks':checks},indent=2)+'\n')
print('PASS',len(checks),'offline checks; target builds and hardware tests remain pending')
