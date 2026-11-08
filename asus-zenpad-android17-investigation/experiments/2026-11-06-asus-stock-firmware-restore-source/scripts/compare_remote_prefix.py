#!/usr/bin/env python3
"""Fixed read-only comparison of the 77 verified remote stock-system chunks.
Default is PLAN_ONLY; no target device is ever contacted.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from audit_restore_source import ROOT, FINGERPRINT, require

RUN = '20261106T155844Z-80cb7ab425df604b'
OEM_MANIFEST_SHA = '853e98e07ca60228f383d322d98ceb951d6910e5afaac480687cdae5d7947140'
COUNT = 77
SSH = ['ssh', '-T', '-i', str(Path.home()/'.ssh/asus_p00a_android17'),
       '-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15',
       '-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556',
       '-o','UserKnownHostsFile='+str(Path.home()/'.ssh/google_compute_known_hosts'),
       'android@IP_REDACTED','python3 -']
WORKER = r'''
import os,stat,hashlib,json
import datetime as dt
from pathlib import Path

def check(path,directory=False):
 s=path.lstat()
 assert s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==(0o700 if directory else 0o600), 'owner/mode'
 assert (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)), 'file type/symlink'
 if not directory: assert s.st_nlink==1, 'unexpected file links'
 return s

def fingerprint(s):
 return (s.st_dev,s.st_ino,s.st_size,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_mtime_ns,s.st_ctime_ns)

base=Path('/srv/android/asus-stock-system-backup')
for ancestor in [Path('/srv'),Path('/srv/android')]:
 s=ancestor.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid in (0,os.getuid()) and not(s.st_mode & 0o002), 'ancestor'
check(base,True);run=base/Q['run'];check(run,True)
marker=run/'RUN.json';check(marker)
assert json.loads(marker.read_bytes())==dict(run=Q['run'],scope='fixed-stock-system-only'), 'owner marker'
rows=[]
for wanted in Q['chunks']:
 index=wanted['index'];assert type(index)is int and 0<=index<77
 p=run/('chunk-%04d.bin'%index)
 before=check(p);assert before.st_size==wanted['bytes']<=33554432
 with p.open('rb') as f:
  assert fingerprint(os.fstat(f.fileno()))==fingerprint(before)
  data=f.read(wanted['bytes']+1)
  after=os.fstat(f.fileno())
 assert len(data)==wanted['bytes'] and fingerprint(after)==fingerprint(before)==fingerprint(check(p)), 'file changed during read'
 actual=hashlib.sha256(data).hexdigest()
 assert actual==wanted['captured_sha256'], 'stored payload changed from two-source verified receipt'
 defined=hashlib.sha256();defined_bytes=0
 import struct
 for start,end,kind,offset in Q['segments']:
  lo=max(start*4096,wanted['offset']);hi=min(end*4096,wanted['offset']+wanted['bytes'])
  if kind!='erase' and lo<hi:
   defined.update(struct.pack('<QQ',lo,hi));defined.update(memoryview(data)[lo-wanted['offset']:hi-wanted['offset']]);defined_bytes+=hi-lo
 rows.append(dict(index=index,bytes=len(data),actual_sha256=actual,
                  captured_digest_matches=True,
                  oem_canonical_matches=actual==wanted['canonical_zero_erase_sha256'],
                  oem_defined_slices_match=defined.hexdigest()==wanted['defined_slices_sha256'] and defined_bytes==wanted['defined_bytes']))
print(json.dumps(dict(scope='fresh remote read-only prefix comparison; not a full backup',run=Q['run'],checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),chunks=rows,checked_bytes=sum(x['bytes'] for x in rows),full_backup_complete=False),sort_keys=True))
'''


def inputs():
    path=ROOT/'evidence/oem-comparison-chunks.json'
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==OEM_MANIFEST_SHA,'OEM manifest changed')
    m=json.loads(raw)
    require(m['target_fingerprint']==FINGERPRINT and m['system_bytes']==3753902080,'OEM target changed')
    old=ROOT.parent/'2026-11-06-asus-stock-system-stream-backup/evidence/runs'/RUN
    receipts=sorted(old.glob('*-chunk_verified.json'))
    require(len(receipts)==COUNT,'Recorded prefix changed')
    rows=[]
    for i,p in enumerate(receipts):
        r=json.loads(p.read_bytes());e=m['chunks'][i]
        require(r['index']==i and r['offset']==e['offset'] and r['bytes']==e['bytes'],'Captured chunk scope changed')
        require(r['sha256_a']==r['sha256_b']==r['remote_sha256']==e['canonical_zero_erase_sha256'],'Captured source/remote/OEM digest mismatch')
        rows.append(dict(e,captured_sha256=r['sha256_a']))
    return dict(run=RUN,chunks=rows,segments=m['segments'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    q=inputs()
    plan=dict(mode='READ_ONLY_SSH' if a.execute else 'PLAN_ONLY',run=RUN,chunks=COUNT,
              bytes=sum(x['bytes'] for x in q['chunks']),device_contacted=False,
              remote_writes=False,full_backup_complete=False)
    if not a.execute:
        print(json.dumps(plan,indent=2));return
    code='Q=json.loads('+repr(json.dumps(q,separators=(',',':')))+')\n'
    # json import precedes the literal request; all target paths are fixed in WORKER.
    script='import json\n'+code+WORKER
    p=subprocess.run(SSH,input=script,text=True,capture_output=True,timeout=180)
    out=ROOT/'evidence'/('remote-prefix-comparison-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    record=dict(plan,argv=SSH,worker_sha256=hashlib.sha256(script.encode()).hexdigest(),
                exit_status=p.returncode,stdout=p.stdout,stderr=p.stderr)
    # Preserve the raw completed SSH reply before interpreting its claims.
    with out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    if p.returncode==0:
        result=json.loads(p.stdout)
        require(result['run']==RUN and len(result['chunks'])==COUNT,'Remote reply scope mismatch')
        require([x['index'] for x in result['chunks']]==list(range(COUNT)),'Remote reply coverage mismatch')
        require(result['checked_bytes']==plan['bytes'],'Remote byte count mismatch')
        require(all(x['captured_digest_matches'] and x['oem_canonical_matches'] and x['oem_defined_slices_match'] for x in result['chunks']),'Actual OEM prefix mismatch')
        record['result']=result
    out.write_text(json.dumps(record,indent=2)+'\n')
    require(p.returncode==0,'Read-only remote comparison failed; see '+str(out))
    print(json.dumps(dict(evidence=str(out),chunks=COUNT,bytes=result['checked_bytes'],
                          captured_and_oem_bytes_match=True,full_backup_complete=False),indent=2))


if __name__=='__main__':
    main()
