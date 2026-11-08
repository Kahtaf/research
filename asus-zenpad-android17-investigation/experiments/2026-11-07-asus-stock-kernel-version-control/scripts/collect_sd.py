"""Collect and preserve one fresh kernel-control report after a new stock boot."""
from pathlib import Path
import argparse,datetime,json,os,secrets,subprocess,uuid
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--control',choices=['original','version2'],required=True);p.add_argument('--previous-boot',required=True);p.add_argument('--target',choices=['IP_REDACTED:5555','DEVICE_SERIAL_REDACTED'],default='IP_REDACTED:5555');a=p.parse_args()
adb='/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools/adb'
env={k:v for k,v in os.environ.items() if not k.startswith(('ADB_','ANDROID_ADB_')) and k!='ANDROID_SERIAL'}
def shell(script):
 token='ASUS_COLLECT_'+secrets.token_hex(16)
 r=subprocess.run([adb,'-s',a.target,'shell','-T','-x','set -eu\n'+script+'\nprintf "'+token+'\\n"\n'],env=env,capture_output=True,text=True,timeout=15)
 assert r.returncode in (0,255) and r.stdout.endswith(token+'\n'),(r.returncode,r.stdout,r.stderr)
 return r.stdout[:-len(token)-1]
identity=shell('getprop ro.serialno\ngetprop ro.product.device\ngetprop sys.boot_completed\ncat /proc/sys/kernel/random/boot_id\ngetenforce\ngetprop ro.adb.secure').splitlines()
assert len(identity)==6 and identity[:3]==['DEVICE_SERIAL_REDACTED','P00A_2','1'] and identity[4:]==['Enforcing','1'] and str(uuid.UUID(identity[3]))==identity[3] and identity[3]!=a.previous_boot,identity
marker=shell('cat /storage/FA06-080C/PROBE.ID');assert marker=='dbbb6afb-dd70-4c35-961e-9c977d7164a8\n'
state={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'control':a.control,'previous_boot_id':a.previous_boot,'new_boot_id':identity[3]}
exist=shell('if test -e /storage/FA06-080C/PROBE.TXT; then echo PRESENT; else echo ABSENT; fi').strip()
if exist=='ABSENT':
 state['outcome']='PROBE_ABSENT_AFTER_NEW_STOCK_BOOT'
else:
 assert exist=='PRESENT'
 report=shell('test "$(wc -c < /storage/FA06-080C/PROBE.TXT)" -le 2048\ncat /storage/FA06-080C/PROBE.TXT')
 expected='run_id=dbbb6afb-dd70-4c35-961e-9c977d7164a8\npid1=1\nsysname=Linux\nrelease=3.18.35\nversion=#'+('1' if a.control=='original' else '2')+' SMP PREEMPT Thu Aug 9 12:33:25 CST 2018\nmachine=aarch64\nstatus=pid1_uname_observed\n'
 (ROOT/'evidence'/('PROBE-'+a.control+'.txt')).write_text(report)
 assert report==expected,report
 dest='RECOMP.TXT' if a.control=='original' else 'VERSION2.TXT'
 state.update(outcome='FRESH_EXPECTED_UNAME_REPORT_OBSERVED',card_report='PROBE.TXT',planned_archive=dest,release='3.18.35',version_number=1 if a.control=='original' else 2)
with (ROOT/'evidence'/('physical-'+a.control+'.json')).open('x') as f:json.dump(state,f,indent=2);f.write('\n')
print(json.dumps(state))
