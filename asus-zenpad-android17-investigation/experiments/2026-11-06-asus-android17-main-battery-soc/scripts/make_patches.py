#!/usr/bin/env python3
"""Build incremental patches using isolated, local subset repositories only."""
from pathlib import Path
import subprocess,shutil,json,hashlib
R=Path(__file__).resolve().parents[1];P=R.parent/'2026-11-06-asus-android17-battery-gauge'
def run(repo,*args,ok=True):
 p=subprocess.run(['git','-C',str(repo),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if ok and p.returncode:raise RuntimeError(p.stdout)
 return p

def init(path,base):
 if path.exists():shutil.rmtree(path)
 shutil.copytree(base,path)
 run(path,'init','-q');run(path,'add','.')
 run(path,'-c','user.name=Offline SOC staging','-c','user.email=ACCOUNT_REDACTED','commit','-qm','Pinned source subset','--no-gpg-sign')

def diff(path,overlay,out):
 shutil.copytree(overlay,path,dirs_exist_ok=True);run(path,'add','-N','.')
 data=run(path,'diff','--binary','--full-index','--no-ext-diff').stdout
 assert data
 (R/'patches'/out).write_text(data)
 run(path,'diff','--check')
 return hashlib.sha256(data.encode()).hexdigest()
repo=R/'evidence/patch-work/kernel';repo.parent.mkdir(parents=True,exist_ok=True)
init(repo,R/'source/kernel-base')
run(repo,'apply','--check','--index',str(P/'patches/0001-asus-p00a-measured-battery.patch'))
run(repo,'apply','--index',str(P/'patches/0001-asus-p00a-measured-battery.patch'))
run(repo,'-c','user.name=Offline SOC staging','-c','user.email=ACCOUNT_REDACTED','commit','-qm','Required previous measurement patch','--no-gpg-sign')
manifest={'kernel_base':'717bb3c9e13ce573cfdd2dda856debd27a0fa17f','prerequisite':{'path':str(P/'patches/0001-asus-p00a-measured-battery.patch'),'sha256':hashlib.sha256((P/'patches/0001-asus-p00a-measured-battery.patch').read_bytes()).hexdigest()},'patches':{}}
name='0002-asus-p00a-checked-main-battery-soc.patch';manifest['patches'][name]={'repository':'kernel','sha256':diff(repo,R/'staged',name)}
for folder,rev,name in [('hardware/interfaces','a0221f11248a924532444fc7de85d41998b9fe1e','0003-android17-health-checked-snapshot.patch'),('frameworks/base','696a5773fa284f53429dbb6c3e5dcc96bf5bd0b3','0004-android17-battery-startup-errors.patch')]:
 repo=R/'evidence/patch-work'/folder.replace('/','-');init(repo,R/'source/platform'/folder)
 manifest['patches'][name]={'repository':folder,'revision':rev,'sha256':diff(repo,R/'integration/platform'/folder,name)}
inputs={}
for p in (R/'staged').rglob('*'):
 if p.is_file():
  rel=p.relative_to(R/'staged');before=R/'source/kernel-after-measurement'/rel
  inputs[str(rel)]={'before':hashlib.sha256(before.read_bytes()).hexdigest() if before.exists() else None,'after':hashlib.sha256(p.read_bytes()).hexdigest()}
manifest['kernel_files']=inputs
guards=['drivers/misc/mediatek/power/mt8163/asus_p00a/'+n for n in ['control.h','policy.h','bq25896.c','battery_status.inc']] + ['arch/arm64/boot/dts/mediatek/asus-p00a.dts','arch/arm64/boot/dts/mediatek/asus8163_tb_380_m_bat_setting.dtsi','drivers/misc/mediatek/include/mt-plat/mt8163/include/mach/mtk_battery_meter.h']
manifest['guard_files']={p:hashlib.sha256((R/'source/kernel-after-measurement'/p).read_bytes()).hexdigest() for p in guards}
manifest['device_files']={str(p.relative_to(R/'integration/device')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'integration/device').rglob('*') if p.is_file()}
(R/'evidence/patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Generated three incremental patches;',len(inputs),'kernel files. No live tree or remote mutation.')
