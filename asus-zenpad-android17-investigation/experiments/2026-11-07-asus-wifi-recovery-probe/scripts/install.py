"""Reuse the reviewed recovery writer through authenticated TCP ADB only."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import socket
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
SOURCE = WORK / '2026-11-06-asus-linux49-minimal-probe-transition/source/adapter.py'
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('reviewed_linux49', SOURCE)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
b = a.b

class Guard:
    def __init__(self, code):
        self.code = code
        self.deadline = time.monotonic() + 600
        self.stopped = False
    def check(self):
        if self.stopped or time.monotonic() >= self.deadline:
            self.stopped = True
            raise b.UncertainTransport('Wi-Fi operation stopped or expired; no further commands')
        a.check_sources()
        if a.code_receipt()['sha256'] != self.code:
            self.stopped = True
            raise b.UncertainTransport('Reviewed recovery code changed')

class WifiTransport(b.AdbRootTransport):
    def __init__(self, directory, journal, guard, run):
        super().__init__(directory, journal, 'install')
        self.guard = guard
        self.boot_id = None
        self.session = b.BASE + '/wifi-linux49-' + run
        self.vault, self.inbox = self.session + '/vault', self.session + '/inbox'
    def command(self, argv, *, script=None, timeout=90):
        self.guard.check()
        try:
            result = super().command(argv, script=script, timeout=timeout)
        except b.UncertainTransport:
            self.guard.stopped = True
            raise
        self.guard.check()
        return result
    def healthy(self):
        super().healthy()
        current = self.adb(['shell', 'cat', '/proc/sys/kernel/random/boot_id'])
        b.require(str(uuid.UUID(current)) == current, 'Invalid stock boot identity')
        if self.boot_id is None:
            self.boot_id = current
            self.journal.event('authenticated_wifi_boot_pin', endpoint=b.ENDPOINT,
                               serial=b.SERIAL, secure_adb=True, boot_id=current)
        b.require(current == self.boot_id, 'Tablet restarted during Wi-Fi operation')
    def root(self, body, label):
        b.require(self.boot_id is not None, 'Fresh authenticated stock boot pin required')
        prefix = '[ "$(cat /proc/sys/kernel/random/boot_id)" = "' + self.boot_id + '" ]\n'
        return super().root(prefix + body, label)
    def read(self):
        data = super().read()
        self.journal.observed(data)
        return data
    def write(self, kind):
        self.guard.check()
        self.journal.state['write_dispatches'].append(dict(source=kind, target=b.BLOCK))
        self.journal.event('write_dispatched', source=kind, target=b.BLOCK)
        return super().write(kind)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='PLAN_ONLY', endpoint=b.ENDPOINT, block=b.BLOCK,
                              usb_enumeration_required=False, reboot=False,
                              device_contacted=False)))
        return 0
    os.umask(0o077)
    for key in list(os.environ):
        if key.startswith(('ADB_', 'ANDROID_ADB_')) or key == 'ANDROID_SERIAL':
            del os.environ[key]
    os.environ['PATH'] = '/opt/homebrew/Caskroom/android-platform-tools/37.0.1/platform-tools' + os.pathsep + os.environ.get('PATH', '/usr/bin:/bin')
    with socket.create_connection(('127.0.0.1', 5037), timeout=2) as server:
        server.sendall(b'000chost:version')
        b.require(server.recv(64).startswith(b'OKAY'), 'Existing ADB server required')
    stock, candidate, local = a.verify_local()
    run = str(uuid.uuid4())
    directory = ROOT / 'private' / run
    directory.mkdir(parents=True, mode=0o700)
    guard = Guard(local['code']['sha256'])
    with a.mutation_lock():
        journal = a.Journal(directory, 'install', run, guard.code)
        journal.state.update(transport=dict(kind='authenticated-adb-tcp', endpoint=b.ENDPOINT),
                             usb_pin_required=False, manual_entry_started=False,
                             user_requested_wifi=True)
        journal.save()
        transport = WifiTransport(directory, journal, guard, run)
        state = a.execute('install', stock, candidate, transport, journal)
        # A fresh complete read may find this exact probe already installed.
        # This is a read-only success, not a new write or a hidden retry.
        if (state['outcome'] == 'refused_or_failed_stop' and not state['write_dispatches']
                and state['partition_status'] == 'exact_candidate' and not guard.stopped):
            guard.check()
            transport.healthy()
            transport.cleanup()
            transport.healthy()
            state = journal.finish('verified_already_candidate', cleanup='verified')
    result = dict(outcome=state['outcome'], run_id=run, evidence=str(directory),
                  cleanup=state['cleanup'], full_p10_sha256=a.FULL_SHA,
                  writes=len(state['write_dispatches']), usb_enumeration_required=False,
                  reboot=False, physical_kernel_boot_proven=False)
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    with (evidence / (run + '.json')).open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps(result), flush=True)
    return 0 if state['outcome'] in ('installed_full_hash_verified', 'verified_already_candidate') and state['cleanup'] == 'verified' else 2

if __name__ == '__main__':
    raise SystemExit(main())
