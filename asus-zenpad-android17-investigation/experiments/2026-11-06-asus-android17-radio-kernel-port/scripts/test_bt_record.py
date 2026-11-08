#!/usr/bin/env python3
import pathlib,subprocess,tempfile,json
r=pathlib.Path(__file__).resolve().parents[1];src=r/'staged/device/asus/p00a/radio';out=r/'evidence/host';out.mkdir(exist_ok=True)
bin=out/'bt-record-test'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(src/'src'),str(src/'src/bt_record.c'),str(src/'tests/bt_record_test.c'),'-o',str(bin)],check=True)
results=[]
with tempfile.TemporaryDirectory(dir=out) as tmp:
 d=pathlib.Path(tmp);p=d/'record'
 def run(case,bad):
  x=subprocess.run([str(bin),str(p),str(int(bad))],capture_output=True,text=True);assert x.returncode==0,(case,x.stdout,x.stderr);results.append(case)
 run('missing',True)
 p.write_bytes(bytes(63));run('short record',True)
 p.write_bytes(bytes(64));run('zero address',True)
 p.write_bytes(bytes([255])*64);run('broadcast address',True)
 p.write_bytes(bytes.fromhex('000046816301')+bytes(58));run('ASUS built-in default rejected',True)
 # Synthetic local-only fixture, never shipped or used as a device identity.
 p.write_bytes(bytes.fromhex('020102030405')+bytes(range(58)));run('valid read-only existing record',False)
 p.write_bytes(bytes.fromhex('010102030405')+bytes(58));run('multicast address',True)
 p.unlink();p.symlink_to(d/'absent');run('symlink',True)
(r/'evidence/bt-record-tests.json').write_text(json.dumps({'compiler':'host cc ASan+UBSan','cases':results,'write_support':'EOPNOTSUPP; no calibration creation/mutation'},indent=2)+'\n')
print(len(results),'BT record scenarios passed')
