from pathlib import Path
import datetime
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
NAME = 'PROJECT_REDACTED'
BASE = ['gcloud', 'compute', 'instances']
FLAGS = ['--project=PROJECT_REDACTED', '--zone=us-central1-a']
state = {'status': 'PREPARING', 'name': NAME, 'project': 'PROJECT_REDACTED',
         'zone': 'us-central1-a', 'commands': [], 'resource_deletion': False,
         'scheduling_change': False, 'labels_change': False,
         'remote_workers_completed': ['50a2ac84', 'e5bf26ca', 'c1184748', '7d1603fa']}


def save():
    target = ROOT / 'evidence/refresh.json'
    temporary = target.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(target)


def run(argv, timeout):
    row = {'argv': argv, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'status': 'DISPATCH_INTENT'}
    state['commands'].append(row)
    save()
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    row.update(status='COMPLETED', exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
    save()
    if result.returncode:
        raise RuntimeError('Cloud command failed; inspect API state, no automatic retry')
    return result.stdout


def describe():
    return json.loads(run(BASE + ['describe', NAME, *FLAGS,
                                 '--format=json(name,status,labels,scheduling,lastStartTimestamp)'], 25))


def main():
    (ROOT / 'evidence').mkdir()
    with (ROOT / 'evidence/started.json').open('x') as stream:
        json.dump(state, stream)
    before = describe()
    assert before['name'] == NAME and before['status'] == 'RUNNING'
    assert before['labels']['owner'] == 'kahtaf'
    assert before['labels']['experiment'] == 'asus-p00a-android17'
    assert before['labels']['created-by'] == 'codex'
    assert before['scheduling']['maxRunDuration']['seconds'] == '86400'
    assert before['scheduling']['instanceTerminationAction'] == 'STOP'
    state['before'] = before
    state['status'] = 'STOPPING_IDLE_BUILDER'
    save()
    run(BASE + ['stop', NAME, *FLAGS, '--quiet'], 240)
    stopped = describe()
    assert stopped['status'] == 'TERMINATED' and stopped['labels'] == before['labels']
    state['stopped'] = stopped
    state['status'] = 'STARTING_EXISTING_BUILDER'
    save()
    run(BASE + ['start', NAME, *FLAGS, '--quiet'], 240)
    after = describe()
    assert after['status'] == 'RUNNING' and after['labels'] == before['labels']
    assert after['scheduling'] == before['scheduling']
    assert after['lastStartTimestamp'] != before['lastStartTimestamp']
    state.update(status='RUNTIME_REFRESHED_EXISTING_SCHEDULING_AND_LABELS_PRESERVED', after=after)
    save()
    print(json.dumps({'status': state['status'], 'lastStartTimestamp': after['lastStartTimestamp'],
                      'maxRunDuration': after['scheduling']['maxRunDuration']}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        state.update(status='UNKNOWN_OR_INCOMPLETE_NO_RETRY', error=type(error).__name__ + ': ' + str(error))
        save()
        raise
