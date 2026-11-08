#!/usr/bin/env python3
"""Offline reproduction. All generated outputs stay within this spike."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
venv=ROOT.parent/'2026-11-05-asus-boot-access-audit/.venv/bin/python'
steps=[('fixture-build',sys.executable,'scripts/build_fixtures.py'),
       ('normal-reachable',str(venv),'scripts/capture_normal_reachable.py'),
       ('normal-lk-audit',sys.executable,'scripts/audit_normal_lk.py'),
       ('python-tests',sys.executable,'tests/test_contract.py'),
       ('source-body-tests',sys.executable,'tests/test_sdk37_sources.py'),
       ('source-excerpts',sys.executable,'scripts/make_excerpts.py'),
       ('review-patch',sys.executable,'scripts/build_review_patch.py'),
       ('integration-patch-test',sys.executable,'tests/test_integration_patch.py')]
results=[]
for name,python,script in steps:
    started=time.monotonic()
    p=subprocess.run([python,str(ROOT/script)],text=True,capture_output=True)
    (ROOT/'evidence'/(name+'.log')).write_text(p.stdout+p.stderr)
    result={'name':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-started,3)};results.append(result)
    print(json.dumps(result),flush=True)
    if p.returncode:raise SystemExit(p.returncode)
(ROOT/'evidence/checks.json').write_text(json.dumps({'status':'PASS','steps':results,'device_operations':0,'remote_mutations':0},indent=2)+'\n')
