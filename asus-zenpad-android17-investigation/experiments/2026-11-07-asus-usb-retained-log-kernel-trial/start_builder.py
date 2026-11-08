from pathlib import Path
import datetime
import json
import subprocess

ROOT = Path(__file__).resolve().parent
E = ROOT / 'evidence'
E.mkdir(exist_ok=True)
RECEIPT = E / 'vm-start.json'
if RECEIPT.exists():
    raise SystemExit('Existing restart receipt: inspect it; do not dispatch another start')
BASE = ['gcloud', 'compute', 'instances']
INSTANCE = 'PROJECT_REDACTED'
FLAGS = ['--project=PROJECT_REDACTED', '--zone=us-central1-a']
FORMAT = 'json'
def describe():
    p = subprocess.run(BASE + ['describe', INSTANCE, *FLAGS, '--format='+FORMAT],
                       capture_output=True, text=True, check=True, timeout=45)
    raw = json.loads(p.stdout)
    result = {k: raw[k] for k in ('id', 'name', 'status', 'labels', 'scheduling')}
    result['disks'] = [{'source': d['source']} for d in raw['disks']]
    result['external_ips'] = [a['natIP'] for n in raw['networkInterfaces']
                              for a in n.get('accessConfigs', []) if 'natIP' in a]
    return result
state = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'start_requests': 0, 'new_resources': False}
def save():
    RECEIPT.write_text(json.dumps(state, indent=2)+'\n')
before = describe()
assert before['id'] == '8549823276971553556'
assert before['labels']['experiment'] == 'asus-p00a-android17'
assert before['labels']['owner'] == 'kahtaf'
assert before['scheduling']['instanceTerminationAction'] == 'STOP'
assert before['scheduling']['maxRunDuration']['seconds'] == '86400'
assert len(before['disks']) == 1
assert before['disks'][0]['source'].endswith('/disks/'+INSTANCE)
assert before['status'] in ('TERMINATED', 'RUNNING')
state['before'] = before
save()
if before['status'] == 'TERMINATED':
    state['start_requests'] = 1
    state['outcome'] = 'start_dispatching'
    save()
    p = subprocess.run(BASE + ['start', INSTANCE, *FLAGS, '--quiet'],
                       capture_output=True, text=True, timeout=240)
    state.update(command_exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
    save()
    assert p.returncode == 0, 'Start failed; inspect receipt, no automatic retry'
after = describe()
assert after['id'] == before['id'] and after['status'] == 'RUNNING'
assert after['labels'] == before['labels'] and after['disks'] == before['disks']
state.update(after=after, outcome='existing_labeled_builder_running',
             ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
print(json.dumps({'outcome': state['outcome'], 'start_requests': state['start_requests']}))
