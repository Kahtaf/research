#!/usr/bin/env python3
"""Replays delivered patches, checks real compiler evidence, and runs behavior suites."""
import hashlib,json,pathlib,shutil,subprocess,tempfile,xml.etree.ElementTree as ET
r=pathlib.Path(__file__).resolve().parents[1];checks=[]
def check(label,ok):
 if not ok:raise AssertionError(label)
 checks.append(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((r/'evidence/kernel-patch-manifest.json').read_text())
for path,item in manifest.items():
 check('output '+path,sha(r/'stagedpatches/kernel-input'/path)==item['after_sha256'])
with tempfile.TemporaryDirectory(prefix='patch-replay-',dir=r/'evidence') as tmp:
 d=pathlib.Path(tmp);shutil.copytree(r/'sourceinputs/kernel-base-717bb3c9',d,dirs_exist_ok=True)
 subprocess.run(['git','init','-q',str(d)],check=True)
 for apply in [False,True,True]:
  cmd=['python3',str(r/'scripts/apply.py'),str(d)]+(['--apply'] if apply else [])
  subprocess.run(cmd,check=True,capture_output=True)
 for path,item in manifest.items():check('replay '+path,sha(d/path)==item['after_sha256'])
 # A conflict must stop preflight, never overwrite another owner's code.
 conflict=next(k for k,v in manifest.items() if v['before_sha256'])
 (d/conflict).write_text('owner change\n')
 q=subprocess.run(['python3',str(r/'scripts/apply.py'),str(d)],capture_output=True)
 check('overlap rejected',q.returncode!=0)
for script in ['test_protocol.py','test_bt_record.py','test_power.py']:
 subprocess.run(['python3',str(r/'scripts'/script)],check=True)
 check(script,True)
for name,digest in json.loads((r/'evidence/firmware-manifest.json').read_text()).items():
 check('generic firmware '+name,sha(r/'sourceinputs/firmware'/name)==digest)
bt=json.loads((r/'evidence/bt-record-abi.json').read_text())
check('adapted BT ELF hash',sha(r/'staged/device/asus/p00a/radio/bluetooth/libbluetooth_mtk.so')==bt['patched_sha256'])
ET.parse(r/'staged/device/asus/p00a/radio/manifest-bluetooth.xml');check('VINTF XML',True)
s=r/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity'
check('PSM is actual protocol',(s/'common/conn_soc/linux/pub/stp_chrdev_bt.c').read_text().count('return wmt_lib_ps_ctrl(arg);')==1)
check('loader defers common init','return misc_register(&p00a_detect);' in (s/'p00a/bootstrap.c').read_text())
check('real reset ordering','reset_control_deassert(rstc)' in (s/'common/conn_soc/mt8163/mtk_wcn_consys_hw.c').read_text())
check('firmware kernel_read','kernel_read(file, offset' in (s/'common/conn_soc/linux/pri/wmt_dev.c').read_text())
check('no credential mutation','current->cred' not in (s/'wlan/gen2/os/linux/gl_kal.c').read_text())
check('calibration required','if (!glLoadNvram(prGlueInfo, prRegInfo))' in (s/'wlan/gen2/os/linux/gl_init.c').read_text())
# No changes to board charging/SOC policy or DT in this deliverable.
check('kernel scope',all(k.startswith('drivers/misc/mediatek/connectivity/') for k in manifest))
linux=r/'evidence/linux-build'
for rel,info in json.loads((r/'evidence/linux-build-manifest.json').read_text()).items():check('compiler evidence '+rel,sha(linux/rel)==info['sha256'])
check('final kernel build exit',(linux/'logs/full-r3.exit').read_text().strip()=='0')
check('userspace build exit',(linux/'logs/userspace-build.exit').read_text().strip()=='0')
config=(linux/'build/.config').read_text()
for opt in ['ASUS_P00A_RADIO','MTK_COMBO','MTK_COMBO_BT','MTK_COMBO_WIFI','MTK_BTIF','MTK_COMBO_CHIP_CONSYS_8163','CFG80211','PM_GENERIC_DOMAINS','REGULATOR_MT6323','RESET_CONTROLLER']:
 check('built config '+opt,'CONFIG_'+opt+'=y\n' in config)
syms=(linux/'build/System.map').read_text()
for symbol in ['mtk_wcn_wmt_func_on','mtk_wcn_stp_send_data','BT_open','WMT_unlocked_ioctl','wlanProbe','p00a_detect_ioctl','mtk_wcn_consys_hw_reg_ctrl']:
 check('linked '+symbol,any(line.endswith(' '+symbol) for line in syms.splitlines()))
if (r/'evidence/compiler-input-sha256.json').exists():
 actual=json.loads((r/'evidence/compiler-input-sha256.json').read_text())
 for path,item in manifest.items():check('compiled source '+path,actual[path]==item['after_sha256'])
(r/'evidence/verification.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'limits':['No hardware/ADB execution','Linux ARM64 static loader build, not Android Soong/HIDL/SELinux validation','Radio kernel fixture omits later parent SOC/platform changes']},indent=2)+'\n')
print(len(checks),'checks passed')
