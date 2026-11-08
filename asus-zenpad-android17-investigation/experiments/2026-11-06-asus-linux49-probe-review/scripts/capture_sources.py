from pathlib import Path
import json,hashlib,re,subprocess,base64
R=Path(__file__).resolve().parents[1]; E=R.parent/'2026-11-06-asus-android17-build-continuation/evidence'; out=R/'source/kernel';out.mkdir(parents=True,exist_ok=True)
receipt=json.loads((E/'combined-source-receipt.json').read_text());freeze=json.loads((E/'snapshot.json').read_text())['files']; pins={}
patch=(E/'combined-from-active-soc.patch').read_bytes().decode()
for part in patch.split('diff --git ')[1:]:
 name=part.splitlines()[0].split(' b/',1)[1]
 if receipt['changes'][name]['before'] is None:
  body=''.join(x[1:] for x in part.splitlines(keepends=True) if x.startswith('+') and not x.startswith('+++'))
  data=body.encode();data=data[:-1] if '\\ No newline at end of file' in part else data;assert hashlib.sha256(data).hexdigest()==receipt['changes'][name]['after'],name
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);pins[name]={'sha256':hashlib.sha256(data).hexdigest(),'origin':'exported patch','matches_receipt':True}
# Read only missing files from the expressly authorized isolated tree. No shell writes or builds.
names=[n for n,v in receipt['changes'].items() if v['before']]
names+=['arch/arm64/kernel/setup.c','drivers/of/fdt.c','init/do_mounts.c','init/main.c','drivers/usb/gadget/udc/core.c','drivers/usb/gadget/configfs.c','drivers/usb/gadget/function/f_fs.c','kernel/reboot.c','drivers/base/core.c','arch/arm64/kernel/process.c','arch/arm64/include/asm/unistd.h','include/uapi/asm-generic/unistd.h','drivers/misc/mediatek/usb20/musb_core.c','drivers/misc/mediatek/usb20/usb20.c','drivers/misc/mediatek/usb20/musb_gadget.c','drivers/misc/mediatek/usb20/mt_usb.c','drivers/misc/mediatek/power/mt8163/asus_p00a/Makefile','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic.c','drivers/watchdog/mtk_wdt.c']
names += ['arch/arm64/mm/init.c','drivers/misc/mediatek/usb20/mt8163/usb20.c','drivers/misc/mediatek/usb20/mt8163/usb20_host.c','drivers/misc/mediatek/usb20/mt8163/usb20_phy.c','drivers/misc/mediatek/connectivity/common/connectivity_build_in_adapter.c','drivers/misc/mediatek/connectivity/common/wmt_build_in_adapter.c','drivers/misc/mediatek/pmic/mt8163/pmic.c','drivers/misc/mediatek/power/mt8163/pmic.c','drivers/misc/mediatek/power/mt8163/pmic_irq.c','drivers/power/supply/mediatek/battery/battery_meter.c','drivers/power/supply/mediatek/battery/switch_charging.c','drivers/misc/mediatek/power/mt8163/battery_meter_hal.c','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_auxadc.inc']
names += ['drivers/misc/mediatek/power/mt8163/pmic_mt6323.c','drivers/misc/mediatek/power/mt8163/pmic_chr_type_det.c']
names += ['drivers/input/keyboard/mediatek/mt8163/hal_kpd.c','drivers/input/keyboard/mediatek/Kconfig','drivers/input/keyboard/mediatek/mtk_kpd.c']
# Prefer exact hash-matching exported base source.
base=R.parent/'2026-11-05-asus-p00a-power-port/sources/kernel';missing=[]
for n in names:
 expected=receipt['changes'].get(n,{}).get('after') or freeze.get(n)
 if isinstance(expected,dict):expected=expected.get('sha256')
 p=base/n
 if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected:
  data=p.read_bytes();q=out/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);pins[n]={'sha256':expected,'origin':'hash-matching local source','matches_receipt':True}
 else:missing.append(n)
remote="import pathlib,json,base64\nr=pathlib.Path('/srv/android/asus-build-continuation/kernel')\nnames="+repr(missing)+"\nprint(json.dumps({n:base64.b64encode((r/n).read_bytes()).decode() if (r/n).is_file() else None for n in names}))\n"
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED','python3 -']
p=subprocess.run(ssh,input=remote.encode(),capture_output=True,check=True,timeout=60)
for n,v in json.loads(p.stdout).items():
 if v is None:pins[n]={'missing':True};continue
 data=base64.b64decode(v);h=hashlib.sha256(data).hexdigest();expected=receipt['changes'].get(n,{}).get('after') or freeze.get(n)
 if isinstance(expected,dict):expected=expected.get('sha256')
 assert h==expected,(n,h,expected)
 q=out/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);pins[n]={'sha256':h,'origin':'authorized read-only SSH isolated kernel','matches_receipt':True}
(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print('pinned',len(pins),'missing',[n for n,v in pins.items() if v.get('missing')])
