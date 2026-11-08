from pathlib import Path
import datetime
import json
import subprocess

ROOT = Path(__file__).resolve().parent
receipt = ROOT/'invocation.json'
if receipt.exists():
    raise SystemExit('Consultation already attempted; inspect its result before another invocation')
argv = ['acpx', '--cwd', str(ROOT), '--model', 'claude-opus-5-5',
        '--format', 'json', '--json-strict', '--approve-all', '--allowed-tools', 'Bash,Read',
        '--max-turns', '12', '--no-terminal', '--no-fs',
        '--mcp-config', str(ROOT/'mcp-empty.json'), '--timeout', '600',
        'claude', 'exec', '--file', str(ROOT/'consultation.txt')]
state = {'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'requested_model':'claude-opus-5-5', 'argv':argv,
         'tool_permissions':'Bash/Read for suppliedpublicevidence + read-onlyexactUSB; no device mutation or cloud access',
         'status':'running'}
receipt.write_text(json.dumps(state,indent=2)+'\n')
with (ROOT/'private/events.ndjson').open('x') as out, (ROOT/'private/stderr.log').open('x') as err:
    try:
        p = subprocess.run(argv, stdout=out, stderr=err)
        state.update(exit=p.returncode, status='completed' if p.returncode==0 else 'failed')
    except BaseException as exc:
        state.update(status='failed', error=type(exc).__name__+': '+str(exc))
state['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps({'status':state['status'],'exit':state.get('exit'),
                  'requested_model':state['requested_model'],'receipt':str(receipt)}),flush=True)
