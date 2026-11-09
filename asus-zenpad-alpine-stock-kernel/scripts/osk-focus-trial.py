#!/usr/bin/env python3
"""Run under a new dbus-run-session on the existing X display; expires in 180s."""

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


HTML = b"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASUS automatic keyboard trial</title>
<style>body{font:24px sans-serif;background:#fff;color:#111;padding:24px}
input,button{font:inherit;padding:16px;margin:12px 0}input{width:85%}
pre{font:16px monospace;white-space:pre-wrap}</style>
<h1>Automatic keyboard trial</h1>
<label for="entry">Trial text</label><br>
<input id="entry" type="text" autocomplete="off" placeholder="Tap here to type">
<br><button id="done" type="button">Done / hide keyboard</button>
<pre id="status">Waiting for initial scripted focus...</pre>
<script>
const entry=document.getElementById('entry'),done=document.getElementById('done');
let commandSequence=0;
function report(reason){
 const data={reason,activeElement:document.activeElement.id,
  value:entry.value,hasFocus:document.hasFocus(),time:new Date().toISOString()};
 document.getElementById('status').textContent=JSON.stringify(data,null,2);
 fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(data)}).catch(()=>{});
}
entry.addEventListener('focus',()=>report('input-focus'));
entry.addEventListener('blur',()=>report('input-blur'));
entry.addEventListener('input',()=>report('input'));
done.addEventListener('focus',()=>report('done-focus'));
done.addEventListener('click',()=>{done.focus();report('done-click')});
window.addEventListener('focus',()=>report('window-focus'));
window.addEventListener('blur',()=>report('window-blur'));
report('loaded');
setTimeout(()=>{entry.focus();report('initial-scripted-focus')},1500);
setInterval(async()=>{
 try{
  const c=await (await fetch('/command',{cache:'no-store'})).json();
  if(c.sequence>commandSequence){
   commandSequence=c.sequence;
   if(c.action==='focus')entry.focus();
   if(c.action==='done')done.focus();
   report('command-'+c.action);
  }
 }catch(e){}
},350);
</script></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path,
                        help='new, nonexistent directory under /tmp')
    args = parser.parse_args()
    if not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        parser.error('launch inside a fresh dbus-run-session')
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'):
        parser.error('DISPLAY and the existing session XAUTHORITY are required')
    baseline = Path('/etc/asus-goodix/firefox-user.js')
    if not baseline.is_file():
        parser.error('missing Firefox baseline: ' + str(baseline))
    firefox = shutil.which('firefox-esr') or shutil.which('firefox')
    if not firefox:
        parser.error('Firefox executable missing')
    if args.directory:
        trial = args.directory.absolute()
        if trial.parent != Path('/tmp') or not trial.name.startswith('asus-osk-trial'):
            parser.error('--directory must be a new /tmp/asus-osk-trial* directory')
        trial.mkdir(mode=0o700)
    else:
        trial = Path(tempfile.mkdtemp(prefix='asus-osk-trial-', dir='/tmp'))

    env = os.environ.copy()
    for key, subdir in [('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'),
                        ('XDG_DATA_HOME', 'data'), ('XDG_STATE_HOME', 'state'),
                        ('XDG_RUNTIME_DIR', 'runtime'), ('TMPDIR', 'tmp')]:
        path = trial / subdir
        path.mkdir(mode=0o700)
        env[key] = str(path)
    env['GSETTINGS_BACKEND'] = 'dconf'
    env['GNOME_ACCESSIBILITY'] = '1'
    env.pop('NO_AT_BRIDGE', None)
    profile = trial / 'profile'
    profile.mkdir(mode=0o700)
    shutil.copyfile(baseline, profile / 'user.js')

    stop = threading.Event()
    lock = threading.RLock()
    started = time.monotonic()
    state = {'trial_directory': str(trial), 'supervisor_pid': os.getpid(),
             'browser_pid': None, 'onboard_pid': None, 'status': 'starting',
             'url': 'http://127.0.0.1:8081/', 'deadline_seconds': 180,
             'display': env['DISPLAY'], 'fixture': None, 'events': [],
             'command': {'sequence': 0, 'action': None}}
    children = []
    logs = []
    server = None
    server_thread = None

    def save():
        with lock:
            state['elapsed_seconds'] = round(time.monotonic() - started, 2)
            temp = trial / 'state.json.new'
            temp.write_text(json.dumps(state, indent=2) + '\n')
            temp.replace(trial / 'state.json')

    def signal_stop(signum, frame):
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, signal_stop)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *values):
            pass

        def reply(self, code, data, kind='application/json'):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.path == '/':
                self.reply(200, HTML, 'text/html; charset=utf-8')
            elif self.path in ('/state', '/command'):
                with lock:
                    value = state if self.path == '/state' else state['command']
                    data = json.dumps(value).encode()
                self.reply(200, data)
            else:
                self.reply(404, b'{}')

        def do_POST(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    raise ValueError('body must be 1..8192 bytes')
                value = json.loads(self.rfile.read(size))
                if not isinstance(value, dict):
                    raise ValueError('JSON object required')
                with lock:
                    if self.path == '/state':
                        state['fixture'] = value
                        state['events'].append(value)
                        state['events'] = state['events'][-40:]
                    elif self.path == '/command' and value.get('action') in ('focus', 'done'):
                        state['command'] = {'sequence': state['command']['sequence'] + 1,
                                            'action': value['action']}
                    else:
                        self.reply(400, b'{"error":"unsupported request"}')
                        return
                    save()
                self.reply(200, b'{"ok":true}')
            except (ValueError, OSError) as error:
                self.reply(400, json.dumps({'error': str(error)}).encode())

    def run_checked(command):
        with (trial / 'setup.log').open('ab') as log:
            log.write(('COMMAND ' + ' '.join(command) + '\n').encode())
            log.flush()
            subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=min(10, max(1, 180 - (time.monotonic() - started))))
        if stop.is_set() or time.monotonic() - started >= 180:
            raise RuntimeError('trial stopped during setup')

    def launch(command, name):
        log = (trial / (name + '.log')).open('ab')
        logs.append(log)
        child = subprocess.Popen(command, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        children.append((name, child))
        (trial / (name + '.pid')).write_text(str(child.pid) + '\n')
        state[name + '_pid'] = child.pid
        save()
        return child

    save()
    print('TRIAL_DIRECTORY=' + str(trial), flush=True)
    try:
        # Activation services inherit the bus daemon's old environment unless updated.
        activation_keys = ['DISPLAY', 'XAUTHORITY', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME',
                           'XDG_DATA_HOME', 'XDG_STATE_HOME', 'XDG_RUNTIME_DIR',
                           'TMPDIR', 'GSETTINGS_BACKEND', 'GNOME_ACCESSIBILITY']
        run_checked(['dbus-update-activation-environment', *activation_keys])
        settings = [
            ('org.gnome.desktop.interface', 'toolkit-accessibility', 'true'),
            ('org.onboard.auto-show', 'enabled', 'true'),
            ('org.onboard.window', 'docking-enabled', 'true'),
            ('org.onboard.window', 'docking-edge', 'bottom'),
            ('org.onboard.window', 'docking-shrink-workarea', 'true'),
            ('org.onboard.auto-show', 'reposition-method-docked', 'none'),
            ('org.onboard.auto-show', 'keyboard-device-detection-enabled', 'false'),
            ('org.onboard.auto-show', 'tablet-mode-detection-enabled', 'false'),
            ('org.onboard.auto-show', 'hide-on-key-press', 'false'),
            ('org.onboard', 'layout', 'Compact'),
        ]
        for schema, key, value in settings:
            run_checked(['gsettings', 'set', schema, key, value])
        server = HTTPServer(('127.0.0.1', 8081), Handler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        onboard = launch(['onboard', '--debug=atspi'], 'onboard')
        browser = launch([firefox, '--no-remote', '--profile', str(profile), state['url']], 'browser')
        state['status'] = 'running'
        save()
        next_report = 0
        while not stop.wait(0.5):
            if (trial / 'STOP').exists():
                state['stop_reason'] = 'STOP file'
                break
            if time.monotonic() - started >= 180:
                state['stop_reason'] = '180 second deadline'
                break
            if onboard.poll() is not None or browser.poll() is not None:
                state['stop_reason'] = 'owned child exited'
                break
            if time.monotonic() >= next_report:
                next_report = time.monotonic() + 5
                with lock:
                    fixture = state['fixture']
                    summary = {'status': state['status'], 'browser_pid': browser.pid,
                               'onboard_pid': onboard.pid,
                               'fixture': fixture, 'directory': str(trial)}
                print('READINESS ' + json.dumps(summary), flush=True)
                save()
        state.setdefault('stop_reason', 'signal')
    except Exception as error:
        state['error'] = str(error)
        state['stop_reason'] = 'error'
        print('TRIAL_ERROR ' + str(error), file=sys.stderr, flush=True)
    finally:
        state['status'] = 'stopping'
        save()
        # Each process has its own session; only groups created here receive TERM.
        for name, child in reversed(children):
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        close_deadline = time.monotonic() + 15
        for name, child in reversed(children):
            try:
                child.wait(timeout=max(0.1, close_deadline - time.monotonic()))
                state[name + '_exit_code'] = child.returncode
            except subprocess.TimeoutExpired:
                state[name + '_cleanup_pending'] = True
                print('TERM_WAIT_EXPIRED ' + name + ' pid=' + str(child.pid), flush=True)
        if server:
            server.shutdown()
            server.server_close()
        if server_thread:
            server_thread.join(timeout=2)
        for log in logs:
            log.close()
        state['status'] = 'cleanup-pending' if any(
            state.get(name + '_cleanup_pending') for name, child in children) else 'stopped'
        save()
        print('TRIAL_FINISHED ' + str(trial / 'state.json'), flush=True)
    return 1 if 'error' in state or state['status'] == 'cleanup-pending' else 0


if __name__ == '__main__':
    sys.exit(main())
