#!/usr/bin/env python3
import argparse,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'build/host-tests';out.mkdir(exist_ok=True)
text=(root/'sources/kernel/drivers/misc/mediatek/include/mt-plat/charging.h').read_text()
enums=[]
for name in ['CHARGING_CTRL_CMD','CHARGER_TYPE','VBUS_STAT_TYPE']:
 m=re.search(r'enum '+name+r'\s*\{.*?\};',text,re.S);assert m;enums.append(m.group())
(out/'platform_enums.h').write_text('\n'.join(enums)+'\n')
cmd=['cc','-std=c11','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-g','-I'+str(out),'-I'+str(root/'sources/kernel/drivers/misc/mediatek/power/mt8163/asus_p00a'),str(root/'tests/power_control_test.c'),'-o',str(out/'power-test')]
r=subprocess.run(cmd,capture_output=True,text=True)
logs=root/'evidence'/a.label;logs.mkdir(exist_ok=True);(logs/'compile.log').write_text(r.stdout+r.stderr)
rows=[dict(step='compile',exit_code=r.returncode,command=cmd)]
if not r.returncode:
 r=subprocess.run([str(out/'power-test')],capture_output=True,text=True);(logs/'run.log').write_text(r.stdout+r.stderr);rows.append(dict(step='run',exit_code=r.returncode));print(r.stdout+r.stderr)
else:print(r.stdout+r.stderr)
(logs/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(r.returncode)
