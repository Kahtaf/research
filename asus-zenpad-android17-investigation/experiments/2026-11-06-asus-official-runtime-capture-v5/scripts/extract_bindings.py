"""One bounded semantic scan: recover only bindings omitted by v4's old index."""
import hashlib,json,os,re,resource,sys,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2));sys.path[:0]=[str(ROOT/'source'),str(ROOT/'scripts')]
from v4_fixture import V4Fixture
from safeio import Tree,need,fingerprint
from ninja import logical,evaluate
start=time.monotonic();g=V4Fixture(ROOT)
projection=json.loads((ROOT/'evidence/projection-scope-names.json').read_bytes());wanted=set(projection['global_names_consulted']);contexts=projection['global_lookup_contexts'];scopes=set()
need(len(wanted)<=2048 and all(len(n)<=4096 for n in wanted),'GRAPH_SCOPE','consulted name budget')
for name,file in contexts:
 scope=g.scopes.context[file][0]
 while scope is not None:scopes.add(scope);scope=g.scopes.parents[scope]
files=sorted(f for f,(scope,prefix) in g.scopes.context.items() if scope in scopes)
positions={name:{(f,line) for f,line,raw in g.rows('variable',name)} for name in wanted}
source=Tree(g.old/'graph-qualification-003/frozen');records=[];stats=[];read_bytes=0;record_bytes=0;new_names=set();head=re.compile(br'([A-Za-z0-9_.-]+)[ \t]*=')
for path in files:
 pin=g.pins[path];lines=0;count=0;continuation=False;pending=None
 with source.open(path) as f:
  need(fingerprint(os.fstat(f.fileno()))==pin['identity'],'FIXTURE_BINDING',path)
  for raw in iter(lambda:f.readline(32*1024**2+1),b''):
   need(len(raw)<=32*1024**2,'GRAPH_BLOCK',path);lines+=1;count+=len(raw);read_bytes+=len(raw);need(read_bytes<=12*1024**3,'GRAPH_SIZE','semantic scan read ceiling')
   if not continuation and raw[:1] not in (b' ',b'\t',b'\n',b'\r',b'#'):
    match=head.match(raw)
    if match:
     name=match[1].decode('ascii')
     if name in wanted and (path,lines) not in positions[name]:pending={'name':name,'graph':path,'line':lines,'parts':[]}
   if pending is not None:
    record_bytes+=len(raw);need(record_bytes<=16*1024**2,'GRAPH_EVIDENCE_SIZE','missing binding records');pending['parts'].append(raw)
   end=len(raw)-1
   while end>=0 and raw[end] in (10,13):end-=1
   dollars=0
   while end>=0 and raw[end]==36:dollars+=1;end-=1
   continuation=bool(dollars%2)
   if pending is not None and not continuation:
    raw_text=b''.join(pending.pop('parts')).decode('utf-8');pending['raw']=raw_text;pending['sha256']=hashlib.sha256(raw_text.encode()).hexdigest()
    value=logical(raw_text)[0].partition('=')[2].lstrip(' ')
    evaluate(value,lambda name:(new_names.add(name) or ''))
    records.append(pending);pending=None
  need(pending is None and count==pin['bytes'] and fingerprint(os.fstat(f.fileno()))==pin['identity']==fingerprint(source.stat(path)),'FIXTURE_BINDING',path)
 stats.append({'path':path,'bytes_streamed':count,'lines':lines,'identity':pin['identity']})
source.close();g.close();new_names-=wanted;usage=resource.getrusage(resource.RUSAGE_SELF)
r={'schema':1,'status':'COMPLETE' if not new_names else 'NEEDS_ADDITIONAL_BINDING_EVIDENCE','purpose':'Repair v4-index omissions for exact consulted variables/scopes, not repeat graph/index QA.','index_identity':g.before,'consulted_names':sorted(wanted),'lookup_context_count':len(contexts),'scanned_graphs':files,'graph_scan':stats,'bytes_streamed':read_bytes,'record_bytes':record_bytes,'records':records,'new_uncovered_references':sorted(new_names),'full_graph_hashing':False,'graph_or_index_copying':False,'new_large_index':False,'actual_output_payloads_opened':False,'input_byte_hard_ceiling':12*1024**3,'record_byte_hard_ceiling':16*1024**2,'cpu_count':1,'address_space_limit_bytes':1024**3,'cpu_seconds_limit':180,'wall_seconds_limit':240,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(usage.ru_utime+usage.ru_stime,3),'max_rss_KiB':usage.ru_maxrss}
with (ROOT/'evidence/supplemental-bindings.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ('records','consulted_names','graph_scan')}));raise SystemExit(0 if not new_names else 1)
