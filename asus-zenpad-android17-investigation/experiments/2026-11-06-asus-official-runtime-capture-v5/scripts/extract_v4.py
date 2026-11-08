"""Bounded read-only v4 record extraction; never rebuild/re-hash the large index."""
import datetime,hashlib,json,os,resource,sqlite3,stat,time
from pathlib import Path
ROOT=Path('/srv/android/asus-official-runtime-capture/preparation-v5')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
start=time.monotonic();old=ROOT.parent/'preparation-v4'
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(s):return [s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
binding=json.loads((ROOT/'inputs/v4-binding.json').read_bytes())
final_bytes=(old/'FINALIZED.json').read_bytes();assert sha(final_bytes)==binding['finalized_sha256']
final=json.loads(final_bytes);assert final['tool_seal_sha256']==binding['tool_seal_sha256'] and final['index_sha256']==binding['index_sha256']
qbytes=(old/'graph-qualification-003/qualification.json').read_bytes();assert sha(qbytes)==binding['qualification_sha256'];q=json.loads(qbytes)
directive_bytes=(old/'evidence/graph-name-inspection.json').read_bytes();assert sha(directive_bytes)==binding['directive_receipt_sha256']
directives=[{**x,'path':x['text'].strip().split(' ',1)[1],'kind':x['text'].split(' ',1)[0]} for x in json.loads(directive_bytes)['directives']]
index=old/'graph-qualification-003/graph-index.sqlite';assert index.resolve()==index
fd=os.open(index,os.O_RDONLY|os.O_NOFOLLOW);before=identity(os.fstat(fd));assert stat.S_ISREG(before[2]) and before[3]==binding['index_bytes']
# v4's full cryptographic index hash was sealed after the final file mutation.
# Any newer data/metadata change or replacement invalidates this shortcut.
seal_time=(old/'FINALIZED.json').stat().st_mtime_ns
assert before[4]<=seal_time and before[5]<=seal_time
for path,pin in q['frozen'].items():assert identity((old/'graph-qualification-003/frozen'/path).lstat())==pin['identity']
db=sqlite3.connect('file:'+str(index)+'?mode=ro&immutable=1',uri=True);db.execute('PRAGMA cache_size=-8192');db.execute('PRAGMA query_only=ON')
records={};size=0;missing=[]
def get(kind,name):
 global size
 key=kind+':'+name
 if key in records:return records[key]
 rows=db.execute('SELECT file,line,text FROM blocks WHERE kind=? AND name=? LIMIT 20',(kind,name)).fetchall()
 if not rows:return None
 assert len(rows)<20 and len({r[2] for r in rows})==1,(kind,name,'ambiguous')
 file,line,raw=rows[0];size+=len(raw.encode());assert size<=16*1024**2 and len(records)<8192
 record={'kind':kind,'name':name,'graph':file,'line':line,'raw':raw,'raw_sha256':sha(raw.encode())};records[key]=record;return record
selector=json.loads((old/'inputs/selector.json').read_bytes())
targets=list(dict.fromkeys(['out/target/product/p00a/'+p for p in selector['required']]+list(selector['generation_outputs'].values())))
# A bounded raw-path closure provides ancestor evidence without payload access.
# Rule/global variable resolution is inspected separately by v5's evaluator.
queue=[(p,0) for p in targets];seen=set()
import re
while queue:
 name,depth=queue.pop(0)
 if name in seen:continue
 assert len(seen)<2048 and depth<12
 seen.add(name);edge=get('edge',name)
 if not edge:missing.append(name);continue
 logical=re.sub(r'\$\n[ \t]*','',edge['raw']).splitlines();rest=logical[0].split(': ',1)[1].split();rule=rest[0]
 if rule!='phony':
  rr=get('rule',rule)
  if rr:
   for var in re.findall(r'\$\{([^}]+)\}|\$([A-Za-z0-9_.-]+)',rr['raw']):
    vn=var[0] or var[1]
    if vn not in ('in','out'):get('variable',vn)
 metadata=any(x in name for x in ('apexkeys.txt','build.prop','/selinux/','/sepolicy/','/vintf/'))
 for token in rest[1:]:
  if token in ('|','||','|@') or '$' in token:continue
  # Private/image path strings are retained in raw evidence, never opened.
  if token.endswith(('.pk8','.key','.pem','.img')):continue
  if token.startswith('out/') and (depth==0 or metadata) and get('edge',token):queue.append((token,depth+1))
# Include all definitions of referenced names so the scoped evaluator may refuse
# ambiguity instead of selecting a convenient definition.
variables=[]
for row in db.execute("SELECT file,line,text,name FROM blocks WHERE kind='variable' AND name IN ('cpFlags','extraCmds','embedFlags','builddir') LIMIT 100"):
 variables.append({'graph':row[0],'line':row[1],'raw':row[2],'name':row[3]})
assert identity(os.fstat(fd))==before==identity(index.lstat());db.close();os.close(fd)
result={'schema':1,'index_binding':binding,'index_identity':before,'index_identity_unchanged':True,'binding_method':'v4 sealed full SHA256 + no post-seal ctime/mtime + exact size + descriptor identity before/after; no full index rehash','frozen_graph_identities_match_v4':True,'frozen_graph_pins':q['frozen'],'includes':directives,'mandatory_targets':targets,'records':list(records.values()),'special_variables':variables,'record_bytes':size,'record_count':len(records),'missing_raw_ancestors':missing,'cpu_count':len(os.sched_getaffinity(0)),'address_space_limit_bytes':1024**3,'cpu_seconds_limit':120,'wall_seconds_limit':180,'elapsed_seconds':round(time.monotonic()-start,3),'cpu_seconds':round(sum(resource.getrusage(resource.RUSAGE_SELF)[:2]),3),'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'no_payload_reads':True}
with (ROOT/'evidence/v4-extracted-records.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
