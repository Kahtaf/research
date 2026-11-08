#!/usr/bin/env python3
"""Validate compiled contexts on existing builder only; never contacts a tablet."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT.parent / '2026-11-06-asus-android17-target-rescue'
REMOTE = '/srv/android/asus-rescue-block-context-fix'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-readonly-validation', action='store_true')
    args = parser.parse_args()
    if not args.execute_readonly_validation:
        print(json.dumps({'mode': 'PLAN_ONLY', 'device_contacted': False, 'remote_fixture': REMOTE}))
        return
    evidence = ROOT / 'evidence/compiled-validation'
    evidence.mkdir(parents=True, exist_ok=False)
    text = (ROOT / 'artifacts/file_contexts').read_bytes()
    hashes = json.loads((DELIVERY / 'artifacts/tools-delivery/hashes.json').read_text())
    payload = {'text_b64': base64.b64encode(text).decode(),
               'text_sha256': hashlib.sha256(text).hexdigest(),
               'tools': {n: hashes[n] for n in ('sefcontext_compile', 'context_lookup', 'policy_constraints')}}
    body = '''
from pathlib import Path
import base64,hashlib,json,subprocess
R=Path('/srv/android/asus-rescue-block-context-fix');R.mkdir(exist_ok=False)
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
P=Path('/srv/android/asus-target-rescue/artifacts/candidate-delivery/rescue-sepolicy')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(P.read_bytes())=='189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
for n,h in payload['tools'].items():assert sha((T/n).read_bytes())==h,n
text=base64.b64decode(payload['text_b64'],validate=True);assert sha(text)==payload['text_sha256']
(R/'file_contexts').write_bytes(text)
commands=[]
def run(argv):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=10)
 commands.append(dict(argv=[str(x) for x in argv],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'commands.json').write_text(json.dumps(commands,indent=2)+'\\n')
 return p
q=run([T/'sefcontext_compile',R/'file_contexts']);assert q.returncode==0,q.stderr
binary=R/'file_contexts.bin'
cases=[]
def lookup(path,mode,expected,alias=None):
 p=run([T/'context_lookup',binary,path,mode]+([alias] if alias else []))
 actual=p.stdout.strip();assert p.returncode==0 and actual==expected,(path,mode,actual,expected)
 cases.append(dict(path=path,mode=mode,expected=expected,alias=alias,passed=True))
roles=[(9,'boot','rescue_boot_device'),(25,'system','rescue_system_device'),(10,'recovery','rescue_recovery_device'),(26,'userdata','rescue_userdata_device')]
links=[]
for part,name,type_name in roles:
 node=f'/dev/block/mmcblk0p{part}'
 alias=f'/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/{name}'
 expected='u:object_r:'+type_name+':s0'
 lookup(node,'060600',expected)
 lookup(alias,'060600',expected)
 lookup(node,'060600',expected,alias)
 lookup(alias,'120777','u:object_r:block_device:s0')
 links.append(alias)
lookup('/dev/block/mmcblk0','060600','u:object_r:rescue_disk_device:s0')
for domain,perms in [('os_rescue','read,getattr'),('ueventd','create,getattr,unlink'),('init','read,getattr')]:
 p=run([T/'policy_constraints',P,'u:r:'+domain+':s0','u:object_r:block_device:s0','lnk_file',perms])
 assert p.returncode==0 and 'allowed=1' in p.stdout,(domain,p.stdout)
for type_name,perms in [('rescue_recovery_device','write'),('rescue_disk_device','write'),('rescue_userdata_device','open,read,write')]:
 p=run([T/'policy_constraints',P,'u:r:os_rescue:s0','u:object_r:'+type_name+':s0','blk_file',perms])
 assert p.returncode==1 and 'allowed=0' in p.stdout,(type_name,p.stdout)
assert sha(P.read_bytes())=='189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842'
result=dict(status='COMPILED_KIND_AND_EXISTING_POLICY_CHECKS_PASS',context_lookups=cases,policy_checks=6,
 text_sha256=sha(text),compiled_sha256=sha(binary.read_bytes()),policy_unchanged_sha256=sha(P.read_bytes()),
 device_operations=0,physical_label_assignment_unproved=True)
(R/'result.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps({k:v for k,v in result.items() if k!='context_lookups'},indent=2))
'''
    program = 'payload=' + repr(payload) + '\n' + body
    (evidence / 'remote-program.py').write_text(program)
    home = Path(os.environ['HOME'])
    options = ['-i', str(home / '.ssh/asus_p00a_android17'), '-o', 'IdentitiesOnly=yes',
               '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'HostKeyAlias=compute.8549823276971553556',
               '-o', 'UserKnownHostsFile=' + str(home / '.ssh/google_compute_known_hosts')]
    result = subprocess.run(['ssh', *options, 'android@IP_REDACTED', 'python3', '-'],
                            input=program, text=True, capture_output=True, timeout=60)
    (evidence / 'stdout.txt').write_text(result.stdout)
    (evidence / 'stderr.txt').write_text(result.stderr)
    (evidence / 'dispatch.json').write_text(json.dumps({'exit': result.returncode, 'remote': REMOTE,
                                                      'device_contacted': False}, indent=2) + '\n')
    print(result.stdout)
    if result.returncode:
        raise RuntimeError('Remote validation failed; inspect retained stderr, do not overwrite fixture')
    for name in ('result.json', 'commands.json', 'file_contexts.bin'):
        target = evidence / name
        subprocess.run(['scp', *options, 'android@IP_REDACTED:' + REMOTE + '/' + name, str(target)],
                       capture_output=True, text=True, timeout=30, check=True)
    captured = json.loads((evidence / 'result.json').read_text())
    assert hashlib.sha256((evidence / 'file_contexts.bin').read_bytes()).hexdigest() == captured['compiled_sha256']


if __name__ == '__main__':
    main()
