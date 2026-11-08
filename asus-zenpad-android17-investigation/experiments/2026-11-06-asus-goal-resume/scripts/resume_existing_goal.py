#!/usr/bin/env python3
"""Apply the user's explicit resume request through the supported app-server API."""
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
THREAD = '01a1a451-715f-7893-81c4-54428f3c8a39'
process = subprocess.Popen(['codex', 'app-server', '--listen', 'stdio://'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)
buffer = b''


def request(identifier, method, params):
    global buffer
    process.stdin.write((json.dumps(dict(id=identifier, method=method, params=params))+'\n').encode())
    process.stdin.flush()
    deadline = time.monotonic()+25
    while time.monotonic() < deadline:
        while b'\n' in buffer:
            line, buffer = buffer.split(b'\n',1)
            if not line.strip(): continue
            value=json.loads(line)
            if value.get('id') == identifier:
                if 'error' in value: raise RuntimeError(value['error'])
                return value['result']
        if selector.select(max(0, deadline-time.monotonic())):
            chunk=os.read(process.stdout.fileno(),65536)
            if not chunk: raise RuntimeError('App-server closed before the response')
            buffer+=chunk
    raise TimeoutError(method)

try:
    request(1,'initialize',dict(clientInfo=dict(name='asus-goal-resume',version='1.0.0'),capabilities=dict(experimentalApi=True)))
    process.stdin.write(b'{"method":"initialized","params":{}}\n');process.stdin.flush()
    before=request(2,'thread/goal/get',dict(threadId=THREAD))
    (ROOT/'evidence/before.json').write_text(json.dumps(before,indent=2)+'\n')
    print('Before:',json.dumps(before))
    response=request(3,'thread/goal/set',dict(threadId=THREAD,status='active',origin='user'))
    (ROOT/'evidence/resume-response.json').write_text(json.dumps(response,indent=2)+'\n')
    after=request(4,'thread/goal/get',dict(threadId=THREAD))
    (ROOT/'evidence/after.json').write_text(json.dumps(after,indent=2)+'\n')
    print('After:',json.dumps(after))
finally:
    process.stdin.close()
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)
