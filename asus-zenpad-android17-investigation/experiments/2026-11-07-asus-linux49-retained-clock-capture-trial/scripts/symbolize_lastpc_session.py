"""Read exact owned build symbols using one owned SSH connection."""
from pathlib import Path
import datetime, importlib.util, json, os, subprocess, sys, tempfile, time
R = Path(__file__).resolve().parents[1]
E = R / 'private/symbolization-lastpc'
VM = 'PROJECT_REDACTED'
OPTIONS = ['--project=PROJECT_REDACTED', '--zone=us-central1-a']
rp = R.parent / '2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec = importlib.util.spec_from_file_location('preserved_remote', rp)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
state = {'events': [], 'read_only_remote_artifact_query': True, 'new_cloud_resources': False}
def save():
    (E / 'lifecycle.json').write_text(json.dumps(state, indent=2) + '\n')
def run(argv, name, timeout=None):
    q = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    (E / (name + '.stdout')).write_text(q.stdout)
    (E / (name + '.stderr')).write_text(q.stderr)
    state['events'].append({'phase': name, 'exit': q.returncode,
                            'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    save()
    return q
def identity(status, name):
    q = run(['gcloud', 'compute', 'instances', 'describe', VM, *OPTIONS,
             '--format=json(id,status,labels,networkInterfaces)'], name)
    q.check_returncode()
    d = json.loads(q.stdout)
    assert d['id'] == '8549823276971553556' and d['status'] == status
    assert all(d['labels'].get(k) == v for k, v in
               {'owner': 'kahtaf', 'purpose': 'rom-build', 'expires': '2026-11-12'}.items())
    assert d['networkInterfaces'][0]['accessConfigs'][0]['natIP'] == 'IP_REDACTED'
assert not (E / 'lifecycle.json').exists()
assert not (R / 'evidence/compiler-receipt.json').exists()
identity('TERMINATED', 'before')
master = False
with tempfile.TemporaryDirectory(prefix='asus-ssh-') as temp:
    os.chmod(temp, 0o700)
    socket = str(Path(temp) / 's')
    try:
        run(['gcloud', 'compute', 'instances', 'start', VM, *OPTIONS], 'start').check_returncode()
        identity('RUNNING', 'running')
        deadline = time.monotonic() + 180
        for attempt in range(1, 10):
            if time.monotonic() >= deadline:
                break
            print('Read-only symbol SSH session attempt ' + str(attempt), flush=True)
            q = run(remote.SSH[:-1] + ['-M', '-S', socket, '-o', 'ControlPersist=120',
                    '-f', '-N', remote.SSH[-1]], 'master-' + str(attempt), timeout=25)
            if q.returncode == 0:
                master = True
                break
            time.sleep(5)
        assert master and Path(socket).is_socket(), 'No authenticated master; compiler not dispatched'
        check = run(remote.SSH[:-1] + ['-S', socket, '-O', 'check', remote.SSH[-1]], 'master-check', timeout=10)
        check.check_returncode()
        (E / 'ssh-control.json').write_text(json.dumps({'socket': socket,
            'same_known_host_alias': 'compute.8549823276971553556',
            'compiler_channel_TCP_fallback_disabled': True}, indent=2) + '\n')
        # Remote exclusive prefix and local dispatch guards still refuse a duplicate compile.
        q = run([sys.executable, '-B', str(R / 'scripts/query_lastpc_symbols.py')], 'query')
        q.check_returncode()
        state['symbol_query_completed'] = True
        save()
    finally:
        if master:
            run(remote.SSH[:-1] + ['-S', socket, '-O', 'exit', remote.SSH[-1]], 'owned-master-exit', timeout=10)
        run(['gcloud', 'compute', 'instances', 'stop', VM, *OPTIONS], 'stop').check_returncode()
        identity('TERMINATED', 'after')
        state['final_status'] = 'TERMINATED'
        save()
print(json.dumps(state, indent=2))
