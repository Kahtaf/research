#!/usr/bin/env python3
from pathlib import Path
import subprocess,shutil,json,hashlib,re,sys
R=Path(__file__).resolve().parents[1];P=R.parent/'2026-11-06-asus-android17-battery-gauge';checks=[]
def check(ok,label):
 checks.append({'check':label,'pass':bool(ok)})
 if not ok:raise AssertionError(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args,required=True):
 p=subprocess.run(['git','-C',str(root),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if required:check(p.returncode==0,'git '+ ' '.join(args[:3])+' in '+root.name+': '+p.stdout[:100])
 return p

def fresh(root,base):
 if root.exists():shutil.rmtree(root)
 shutil.copytree(base,root);git(root,'init','-q');git(root,'add','.')
 git(root,'-c','user.name=Offline replay','-c','user.email=ACCOUNT_REDACTED','commit','-qm','Pinned source subset','--no-gpg-sign')

def tables(text):
 text=re.sub(r'/\*.*?\*/','',text,flags=re.S)
 return {k:[int(x.strip('()'),0) for x in v.split()] for k,v in re.findall(r'\b((?:battery|r)_profile_t[0-3]|q_max_\w+)\s*=\s*<([^>]+)>',text)}
try:
 old=json.loads((R/'evidence/previous-spike-before.json').read_text())
 current={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file()}
 check(current==old,'entire prior measurement spike byte-for-byte unchanged')
 initial=json.loads((R/'evidence/source-manifest.json').read_text())
 for p,h in initial.items():check(sha(R/'source'/p)==h,'immutable input '+p)
 for kind,prefix in [('kernel','kernel-base'),('platform','platform')]:
  m=json.loads((R/f'evidence/{kind}-additional-source.json').read_text())
  if kind=='kernel':
   for p,h in m['sha256'].items():check(sha(R/'source'/prefix/p)==h,'pinned extra kernel source '+p)
  else:
   for v in m:check(sha(R/'source/platform'/v['repository']/v['path'])==v['sha256'],'pinned extra platform source '+v['path'])
 manifest=json.loads((R/'evidence/patch-manifest.json').read_text())
 for name,v in manifest['patches'].items():check(sha(R/'patches'/name)==v['sha256'],'patch hash '+name)
 check(sha(P/'patches/0001-asus-p00a-measured-battery.patch')==manifest['prerequisite']['sha256'],'immutable prerequisite patch hash')
 replay=R/'evidence/replay/kernel';fresh(replay,R/'source/kernel-base')
 wrong=git(replay,'apply','--check',str(R/'patches/0002-asus-p00a-checked-main-battery-soc.patch'),required=False)
 check(wrong.returncode!=0,'SOC patch rejects kernel base without prerequisite measurement patch')
 for patch in [P/'patches/0001-asus-p00a-measured-battery.patch',R/'patches/0002-asus-p00a-checked-main-battery-soc.patch']:
  git(replay,'apply','--check','--index','--whitespace=error-all',str(patch))
  git(replay,'apply','--index','--whitespace=error-all',str(patch))
 for p,v in manifest['kernel_files'].items():check(sha(replay/p)==v['after']==sha(R/'staged'/p),'exact kernel replay '+p)
 # No other prerequisite files may drift, including all charger policy/ADC routes.
 for p in (R/'source/kernel-after-measurement').rglob('*'):
  if p.is_file() and str(p.relative_to(R/'source/kernel-after-measurement')) not in manifest['kernel_files']:
   check((replay/p.relative_to(R/'source/kernel-after-measurement')).read_bytes()==p.read_bytes(),'unchanged kernel dependency '+str(p.relative_to(R/'source/kernel-after-measurement')))
 p=subprocess.run([sys.executable,str(R/'scripts/apply_kernel.py'),str(replay)],text=True,capture_output=True)
 check(p.returncode==0 and 'already present' in p.stdout,'idempotent exact application preflight')
 for repo,name in [('hardware/interfaces','0003-android17-health-checked-snapshot.patch'),('frameworks/base','0004-android17-battery-startup-errors.patch')]:
  path=R/'evidence/replay'/repo.replace('/','-');fresh(path,R/'source/platform'/repo)
  git(path,'apply','--check','--index','--whitespace=error-all',str(R/'patches'/name));git(path,'apply','--index','--whitespace=error-all',str(R/'patches'/name))
  for p in (R/'integration/platform'/repo).rglob('*'):
   if p.is_file():check((path/p.relative_to(R/'integration/platform'/repo)).read_bytes()==p.read_bytes(),'exact platform replay '+str(p.relative_to(R/'integration/platform')))
 dt=R/'source/kernel-after-measurement/arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi'
 original=R/'source/asus-3.18/arch/arm64/boot/dts/asus8163_tb_380_m_bat_setting.dtsi'
 model=tables(dt.read_text());stock=tables(original.read_text())
 check(model==stock,'all eight raw model tables and eight Qmax constants exactly equal original ASUS source')
 for key,values in model.items():
  if 'profile' in key:check(len(values)==208,'all 104 pairs retained: '+key)
 check((replay/dt.relative_to(R/'source/kernel-after-measurement')).read_bytes()==dt.read_bytes(),'DT and all charge limits unchanged after measurement predecessor')
 board=(replay/'arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text()
 check(not re.search(r'^\s*asus,allow-battery-charging\b',board,re.M),'charging opt-in remains absent')
 cfg=(replay/'arch/arm64/configs/asus_p00a_defconfig').read_text()
 for key in ['ASUS_P00A_MAIN_BATTERY_SOC','ASUS_P00A_BATTERY_DIAGNOSTIC','ASUS_P00A_BQ25896','MTK_SMART_BATTERY']:
  check(f'CONFIG_{key}=y' in cfg,'required config '+key)
 for key in ['MTK_MULTI_BAT_PROFILE_SUPPORT','MTK_BATTERY_LIFETIME_DATA_SUPPORT']:
  check(f'# CONFIG_{key} is not set' in cfg,'unsupported config disabled '+key)
 # Preprocess the production functions/config branches and reject reachable
 # old OAM integration, uninitialized charging or optional 10 C model use.
 meter=(replay/'drivers/power/supply/mediatek/battery/battery_meter.c').read_text()
 source=re.sub(r'^\s*#include[^\n]*','',meter,flags=re.M)
 defines=''.join('#define '+k+' 1\n' for k in re.findall(r'^(CONFIG_\w+)=y$',cfg,re.M))+'#define SOC_BY_SW_FG 1\n'
 pre=subprocess.run(['clang','-E','-P','-x','c','-'],input=defines+source,text=True,capture_output=True)
 check(pre.returncode==0,'selected kernel meter branches preprocess on host')
 check('oam_car_1 = oam_car_1 +' not in pre.stdout and 'oam_car_2 = oam_car_2 +' not in pre.stdout,'old resume sleep-current advancement unreachable')
 check('oam_i_2 = (((oam_v_ocv_2' not in pre.stdout,'unchecked old OAM advancement unreachable')
 check('unsigned int charging_enable = false;' in meter,'legacy oam_init charging_enable initialized false')
 # The already-compiled source extracts test dispatch/reset/PM/thermal behavior.
 extracted=(R/'evidence/host/include/model_functions.h').read_text()
 pp=subprocess.run(['clang','-E','-P','-x','c','-'],input='#define CONFIG_ASUS_P00A_MAIN_BATTERY_SOC 1\n'+extracted,text=True,capture_output=True)
 # Only profile getters retain the generic intermediate-axis branch; the four
 # interpolators themselves are tested against original stock source.
 check(pp.returncode==0,'four-axis model functions preprocess')
 health=(R/'integration/platform/hardware/interfaces/health/aidl/default/Health.cpp').read_text()
 header=(R/'integration/platform/hardware/interfaces/health/aidl/default/include/health-impl/Health.h').read_text()
 loop=(R/'integration/platform/hardware/interfaces/health/aidl/default/HalHealthLoop.cpp').read_text()
 dev=(R/'integration/device/asus/p00a/health/Health.cpp').read_text()
 check('getHealthInfo(HealthInfo* out) override final' in header,'aggregate getter remains final')
 check('auto status = ReadBatterySnapshot(out);' in health,'aggregate error hook is in final getter')
 check('CHECK(res.isOk())' not in loop and 'AdjustWakealarmPeriods(charger_online());' in loop,'Health loop retries failed aggregate without abort')
 check('OnHealthInfoChanged' not in dev and 'getHealthInfo(' not in dev,'device does not replace callbacks or override final getter')
 monitor=(R/'source/platform/system/core/healthd/BatteryMonitor.cpp').read_text();section=monitor[monitor.index('void BatteryMonitor::initWithBatteryDevice'):monitor.index('void BatteryMonitor::init(')]
 for field in re.findall(r'if \(mHealthdConfig->(\w+)\.empty\(\)\)',section):
  check(re.search(r'config->'+field+r' = "/sys/class/power_supply/battery/[^"/]+";',dev)!=None,'main battery pinned: '+field)
 framework=(R/'integration/platform/frameworks/base/services/core/java/com/android/server/BatteryService.java').read_text()
 callback=(R/'integration/platform/frameworks/base/services/core/java/com/android/server/health/HealthRegCallbackAidl.java').read_text()
 check('if (mHealthInfo != null)' in framework and 'No valid initial battery sample' in framework,'framework startup waits for actual initial sample')
 check('catch (RemoteException | ServiceSpecificException e)' in callback,'initial update tolerates reported transient service error')
 host=json.loads((R/'evidence/host-checks.json').read_text())
 for name,result in host['tests'].items():check(result['compile_returncode']==0 and result['run_returncode']==0,'host sanitizer suite '+name)
 for p,h in host['tested_inputs'].items():check(sha(R/p)==h,'tested production input current: '+p)
 for p,h in manifest['device_files'].items():check(sha(R/'integration/device'/p)==h,'device handoff hash '+p)
 report={'scope':'Strict local subset replay and source consistency; NOT full kernel/Android compilation','passed':len(checks),'checks':checks}
 (R/'evidence/source-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS:',len(checks),'source/replay checks; measurement predecessor and own-spike boundaries preserved.')
except Exception:
 (R/'evidence/source-checks.json').write_text(json.dumps({'passed':sum(x['pass'] for x in checks),'checks':checks},indent=2)+'\n')
 raise
