from pathlib import Path
import datetime,json,subprocess,signal
ROOT=Path(__file__).resolve().parent
TARGET='abliteration-ai/abliterated-model-large-v2'
pth=ROOT/'invocation.json'
if pth.exists():raise SystemExit('Already attempted; inspect preserved result')
argv=['acpx','--cwd',str(ROOT),'--model',TARGET,'--format','json','--json-strict','--deny-all','--allowed-tools','','--max-turns','1','--no-terminal','--no-fs','--mcp-config',str(ROOT/'mcp-empty.json'),'--timeout','600','opencode','exec','--file',str(ROOT/'consultation.txt')]
s={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_model':TARGET,'agent':'opencode','tools':'none; supplied public evidence only','status':'running','argv':argv};pth.write_text(json.dumps(s,indent=2)+'\n')
chunks=[];model=None;names=[];verified=False;cancelled=False;events=[];select_ids=set()
with (ROOT/'private/events.ndjson').open('x') as out,(ROOT/'private/stderr.log').open('x') as err:
 p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
 for i,line in enumerate(p.stdout):
  out.write(line);out.flush()
  try:d=json.loads(line)
  except ValueError:continue
  method=d.get('method');args=d.get('params',{});res=d.get('result',{});u=args.get('update',{})
  if method=='session/set_model' and args.get('modelId')==TARGET:select_ids.add(d.get('id'))
  if method=='session/set_config_option' and args.get('configId')=='model' and args.get('value')==TARGET:select_ids.add(d.get('id'))
  if d.get('id') in select_ids and 'result' in d:
   s['model_selection_acknowledged']=True
  updates=[]
  if isinstance(res,dict) and isinstance(res.get('models'),dict):
   cur=res['models'].get('currentModelId')
   if cur:updates.append(cur)
  for opts in (res.get('configOptions',[]) if isinstance(res,dict) else [],u.get('configOptions',[])):
   for x in opts:
    if x.get('id')=='model':
     cur=x.get('currentValue')
     if cur:updates.append(cur)
  if u.get('sessionUpdate')=='current_model_update' and u.get('currentModelId'):updates.append(u['currentModelId'])
  for cur in updates:
   model=cur;events.append({'line':i,'selected':model})
   if model==TARGET:verified=True
   elif verified and not cancelled:
    cancelled=True;s['reason']='Unexpected model change';p.send_signal(signal.SIGINT)
  (ROOT/'model-confirmation.json').write_text(json.dumps({'requested':TARGET,'observed_selected':model,'target_observed':verified,'selection_acknowledged':s.get('model_selection_acknowledged',False),'events':events},indent=2)+'\n')
  if u.get('sessionUpdate')=='agent_message_chunk' and u.get('content',{}).get('type')=='text':
   chunks.append(u['content'].get('text',''));(ROOT/'RECOMMENDATION.md').write_text(''.join(chunks))
   if not cancelled and 'Model fallback' in ''.join(chunks)[-2000:]:
    cancelled=True;s['reason']='Fallback notification';p.send_signal(signal.SIGINT)
 s['exit']=p.wait()
s['status']='cancelled_unexpected_model' if cancelled else 'completed' if s['exit']==0 else 'failed';s['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['selected_model']=model;s['target_model_observed']=verified;s['answer_chars']=sum(map(len,chunks));pth.write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({k:s.get(k) for k in ('status','exit','requested_model','selected_model','target_model_observed','model_selection_acknowledged','answer_chars')}),flush=True)
