#!/usr/bin/env python3
"""Read-only observer; PLAN ONLY unless --observe. Never run as part of offline QA.

USB topology is pinned during a fresh exact-stock preflight by the parent. Missing
USB topology is a refusal, not permission to pick the generic diagnostic serial.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

STOCK = 'DEVICE_SERIAL_REDACTED'
DIAGNOSTIC = '0123456789ABCDEF'
MARKER = b'ASUS RAM-only diagnostic os-rescue-v1'
FINGERPRINT = 'asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys'

class Refused(Exception): pass

def parse_devices(text):
    result=[]
    for line in text.splitlines():
        if not line or line.startswith('List of devices'): continue
        words=line.split()
        if len(words)<2 or words[0].startswith('*'): raise Refused('Unexpected inventory line')
        row={'serial':words[0],'state':words[1]}
        for word in words[2:]:
            if ':' not in word: raise Refused('Malformed inventory')
            key,value=word.split(':',1)
            if key in row: raise Refused('Duplicate inventory field')
            row[key]=value
        result.append(row)
    return result

def select(rows, pin):
    if pin.get('stock_serial')!=STOCK or not pin.get('usb') or pin.get('stock_fingerprint')!=FINGERPRINT:
        raise Refused('Fresh exact-stock physical USB pin required')
    if pin.get('stock_device')!='P00A_2' or not pin.get('stock_product') or not pin.get('stock_model'):
        raise Refused('Missing reviewed stock product/model/device')
    candidates=[r for r in rows if r['serial'] in (STOCK,DIAGNOSTIC) or r.get('usb')==pin['usb']]
    if not candidates:return None
    if len(candidates)!=1: raise Refused('Ambiguous devices; no selection')
    r=candidates[0]
    if r.get('usb')!=pin['usb']: raise Refused('USB physical topology missing or changed')
    if not re.fullmatch(r'[0-9]+',r.get('transport_id','')): raise Refused('Transport ID required')
    if r['serial']==DIAGNOSTIC:
        expected={'state':'recovery','product':'p00a_diagnostic','model':'P00A_RAM_diagnostic','device':'p00a'}
    elif r['serial']==STOCK:
        expected={'state':'device','product':pin['stock_product'],'model':pin['stock_model'],'device':'P00A_2'}
    else: raise Refused('Unexpected device at physical port')
    if any(r.get(k)!=v for k,v in expected.items()):raise Refused('Identity/state mismatch')
    return r

def validate_report(data, rc):
    return (rc==0 and MARKER in data and b'END_DIAGNOSTIC' in data
            and b'REPORT_ENDPOINT uid=2000 context=u:r:shell:s0' in data
            and b'androidboot.serialno='+STOCK.encode() in data)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pin',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--observe',action='store_true')
    a=ap.parse_args();pin=json.loads(a.pin.read_text())
    select([],pin)
    if not a.observe:
        print(json.dumps({'mode':'PLAN_ONLY','pin':pin,'device_contacted':False}));return
    a.out.mkdir(mode=0o700,parents=True,exist_ok=False)
    def cmd(args): return subprocess.run(['adb',*args],capture_output=True,timeout=12)
    seen=False;report_ok=False;end=time.monotonic()+420
    with (a.out/'events.jsonl').open('x') as log:
        while time.monotonic()<end:
            # Any failure stops this observer. No transport retry/reboot/repair.
            inv=cmd(['devices','-l'])
            if inv.returncode:raise Refused('Inventory failed')
            row=select(parse_devices(inv.stdout.decode()),pin)
            event={'time':time.time(),'row':row}
            if row:
                # transport_id addresses this exact enumeration, never -s generic serial.
                args=['-t',row['transport_id'],'shell']
                if row['serial']==DIAGNOSTIC:
                    seen=True
                    if not report_ok:
                        p=cmd(args+['report'])
                        name=f'report-{time.time_ns()}.txt';(a.out/name).write_bytes(p.stdout)
                        report_ok=validate_report(p.stdout,p.returncode)
                        event.update(report_complete=report_ok,returncode=p.returncode,file=name,sha256=hashlib.sha256(p.stdout).hexdigest())
                elif seen:
                    checks=[cmd(args+['getprop',prop]) for prop in ('ro.serialno','ro.build.fingerprint','ro.build.version.sdk','sys.boot_completed')]
                    expect=[STOCK,FINGERPRINT,'24','1']
                    returned=all(p.returncode==0 and p.stdout.decode().strip()==v for p,v in zip(checks,expect))
                    event.update(stock_returned=returned,report_complete=report_ok,recovery_restored=False)
                    log.write(json.dumps(event)+'\n');log.flush()
                    if returned:return
            log.write(json.dumps(event)+'\n');log.flush();time.sleep(2)
    raise Refused('Observation deadline; parent assesses screen/physical return')

if __name__=='__main__':main()
