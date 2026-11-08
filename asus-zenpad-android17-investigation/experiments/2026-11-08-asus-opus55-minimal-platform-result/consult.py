from pathlib import Path
import subprocess,json,datetime,signal,os
ROOT=Path(__file__).resolve().parent
receipt=ROOT/'invocation.json'
if receipt.exists():raise SystemExit('Already attempted')
argv=['acpx','--cwd',str(ROOT),'--model','claude-opus-5-5','--format','json','--json-strict','--deny-all','--allowed-tools','','--max-turns','1','--no-terminal','--no-fs','--mcp-config',str(ROOT/'mcp-empty.json'),'--timeout','600','claude','exec','--file',str(ROOT/'consultation.txt')]
s={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_model':'claude-opus-5-5','status':'running','fallback_allowed':False,'tools':'none','argv':argv};receipt.write_text(json.dumps(s,indent=2)+'\n')
chunks=[];models=[];fallback=False
with (ROOT/'private/events.ndjson').open('x') as out,(ROOT/'private/stderr.log').open('x') as err:
 p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
 for line in p.stdout:
  out.write(line);out.flush()
  try:d=json.loads(line)
  except ValueError:continue
  u=d.get('params',{}).get('update',{})
  for opts in (d.get('result',{}).get('configOptions',[]),u.get('configOptions',[])):
   for x in opts:
    if x.get('id')=='model':models.append(x)
  if u.get('sessionUpdate')=='agent_message_chunk' and u.get('content',{}).get('type')=='text':
   t=u['content'].get('text','');chunks.append(t)
   (ROOT/'OPUS-RESPONSE.md').write_text(''.join(chunks))
   if not fallback and ('Model fallback' in t or 'Model fallback' in ''.join(chunks)[-2000:]):
    fallback=True;s['fallback_notification_received']=True;p.send_signal(signal.SIGINT)
 s['exit']=p.wait()
s['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['status']='stopped_unauthorized_fallback' if fallback else 'completed' if s['exit']==0 else 'failed'
receipt.write_text(json.dumps(s,indent=2)+'\n')
sel=models[-1] if models else {};wanted=sel.get('currentValue')
def names(items):
 for i in items:
  if i.get('value')==wanted:yield i.get('name')
  if isinstance(i.get('options'),list):yield from names(i['options'])
conf={'selected':wanted,'name':next(names(sel.get('options',[])),None),'fallback_seen':fallback};(ROOT/'model-confirmation.json').write_text(json.dumps(conf,indent=2)+'\n')
print(json.dumps({'status':s['status'],'exit':s['exit'],'model':conf,'public_response':str(ROOT/'OPUS-RESPONSE.md')}),flush=True)
