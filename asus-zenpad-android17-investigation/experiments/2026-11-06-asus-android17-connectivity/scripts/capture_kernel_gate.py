#!/usr/bin/env python3
"""Capture current builder connectivity prerequisites without remote mutations."""
import json
from remote_read import run, ROOT
CODE = r'''
import hashlib, json, pathlib, re, subprocess
kernel = pathlib.Path('/srv/android/asus-android17/kernel-bpf-fd')
build = pathlib.Path('/srv/android/asus-android17/build-bpf-fd')
source_names = ['wmt_dev.c', 'stp_chrdev_bt.c', 'wmt_chrdev_wifi.c', 'gl_init.c', 'wmt_ic_soc.c']
found = {name: [str(p.relative_to(kernel)) for p in kernel.rglob(name)] for name in source_names}
map_path = build/'System.map'
map_text = map_path.read_text()
symbols = {l.split()[-1] for l in map_text.splitlines() if l.split()}
required = ['WMT_unlocked_ioctl','BT_open','WIFI_write','wlanProbe','mtk_wcn_wmt_func_on','mtk_wcn_stp_send_data']
config = (build/'.config').read_text()
config_lines = [l for l in config.splitlines() if re.match(r'(?:# )?CONFIG_(?:MTK_COMBO|MTK_BTIF|BT\b|CFG80211\b|COMPAT\b|MODULES\b)', l)]
result = {
 'kernel_path': str(kernel),
 'kernel_head': subprocess.check_output(['git','-C',str(kernel),'rev-parse','HEAD'],text=True).strip(),
 'system_map_sha256':hashlib.sha256(map_path.read_bytes()).hexdigest(),
 'config_sha256':hashlib.sha256((build/'.config').read_bytes()).hexdigest(),
 'config_lines':config_lines,
 'source_files':found,
 'linked_required_symbols':{s:s in symbols for s in required},
 'linked_adapter_symbols': sorted(s for s in symbols if s.startswith(('wmt_export_', 'mtk_wcn_btif_'))),
 'loadable_modules': [str(p.relative_to(build)) for p in build.rglob('*.ko')],
 'scope':'Source and built kernel only; no device operations or hardware claims',
}
print(json.dumps(result,indent=2))
'''
if __name__ == '__main__':
    data = json.loads(run(CODE))
    data['transport_gate_passed'] = all(data['linked_required_symbols'].values())
    (ROOT/'evidence/kernel-gate.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
