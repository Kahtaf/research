#!/usr/bin/env python3
"""Pinned fixed-path metadata query. This receipt is never production admission."""
from pathlib import Path
import argparse,hashlib,json,os,re,resource,signal,stat,struct,subprocess,sys
ROOT=Path('/srv/android/asus-sdk37-host-metadata-resolvers-20261106')
I=ROOT/'inputs-r4'
PATHS=('/system/build.prop','/system/bin/init','/system/bin/run-as','/system/vendor/etc/selinux/vendor_file_contexts')
SLOTS=('system','vendor','oem','odm','product','system_ext')

def need(ok,why):
 if not ok:raise ValueError(why)

def bounded():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2));signal.alarm(90)

def sha(b):return hashlib.sha256(b).hexdigest()
def pin(v):need(type(v)is str and re.fullmatch('[a-f0-9]{64}',v)is not None,'Missing/invalid SHA256');return v

def pairs(items):
 d={}
 for k,v in items:need(k not in d,'Duplicate JSON key');d[k]=v
 return d

def keys(d,k):need(type(d)is dict and set(d)==set(k),'Missing/unknown fields')

def snap(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode),'Require ordinary file');return dict(dev=s.st_dev,ino=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)

def read(p,expected,max_size=1024**2):
 p=Path(p);need(p.is_absolute() and p.resolve(strict=True)==p,'Require real absolute path, no symlinks')
 before=snap(p);need(before['bytes']<=max_size,'Input too large');b=p.read_bytes();need(sha(b)==pin(expected),'Pinned input mismatch: '+str(p));need(snap(p)==before,'Input changed');return b,before

def validate_override(b):
 offset=0;records=0
 while offset<len(b):
  need(len(b)-offset>=16,'Truncated fs_config header')
  length,mode,uid,gid,caps=struct.unpack_from('<HHHHQ',b,offset)
  need(length>16 and length%8==0 and offset+length<=len(b),'Malformed fs_config record length')
  prefix=b[offset+16:offset+length];z=prefix.find(b'\0')
  need(z>0 and not any(prefix[z:]),'Missing prefix NUL or invalid padding')
  prefix[:z].decode('utf-8');need(mode&~0o7777==0,'Unexpected mode/type bits')
  offset+=length;records+=1
 return records

def clean_env():
 env={k:v for k,v in os.environ.items()if not k.startswith('LD_')};env.update(LC_ALL='C',TMPDIR=str(ROOT/'tmp'));return env

def invoke(tool,args,output):
 cmd=[str(I/'lib64/ld-linux-x86-64.so.2'),'--inhibit-cache','--library-path',str(I/'lib64'),str(tool),*map(str,args)]
 p=subprocess.run(cmd,env=clean_env(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,preexec_fn=bounded)
 result=dict(argv=cmd,exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'))
 if output is not None:
  output.parent.mkdir(parents=True,exist_ok=True);output.with_suffix('.stdout').write_bytes(p.stdout);output.with_suffix('.stderr').write_bytes(p.stderr);output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
 return result

def tools():
 d=json.loads((ROOT/'qualified-tools.json').read_text())
 for r in d['pinned_files']:read(r['path'],r['sha256'],64*1024**2)
 return d

def query(path,expected,output):
 need(sys.byteorder=='little','Qualified host ABI is little endian')
 raw,_=read(path,expected);d=json.loads(raw,object_pairs_hook=pairs)
 keys(d,('schema','scope','binding','capture_root','native_target_out','search_slots','contexts','tool_group_sha256'))
 need(d['schema']=='asus-sdk37-metadata-query-inputs/v1','Wrong schema')
 need(d['scope']in ('FIXTURE_ONLY','PARENT_CAPTURE_QUERY'),'This is a scoped query, never product admission')
 if d['scope']=='FIXTURE_ONLY':keys(d['binding'],('fixture_id',))
 else:
  keys(d['binding'],('build_id','complete_sha256','source_binding_sha256','installed_content_receipt_sha256'))
  for k in ('complete_sha256','source_binding_sha256','installed_content_receipt_sha256'):pin(d['binding'][k])
 need(type(d['native_target_out'])is str and Path(d['native_target_out']).is_absolute(),'Missing native TARGET_OUT source binding')
 group=tools();need(sha((ROOT/'qualified-tools.json').read_bytes())==pin(d['tool_group_sha256']),'Tool group mismatch')
 capture=Path(d['capture_root']);need(capture.is_absolute() and capture.resolve(strict=True)==capture,'Invalid capture root')
 target=capture/'layout/system';need(target.is_dir() and target.resolve()==target,'Missing canonical captured TARGET_OUT')
 slots=d['search_slots'];need(type(slots)is list and len(slots)==6,'Require explicit six search slots')
 snapshots={};absent=[];record_counts={}
 for slot,row in zip(SLOTS,slots):
  keys(row,('slot','state','sha256'));need(row['slot']==slot,'Wrong/duplicate search slot')
  p=capture/'layout'/slot/'etc/fs_config_files'
  if row['state']=='present':
   b,identity=read(p,row['sha256']);record_counts[slot]=validate_override(b);snapshots[str(p)]=identity
  else:
   need(row['state']=='absent' and row['sha256']is None,'Missing explicit absence')
   need(not os.path.lexists(p),'Declared-absent captured file exists')
   # Native fs_config can fall back to these absolute host paths; no content is read here.
   host=Path('/')/slot/'etc/fs_config_files';need(not os.path.lexists(host),'Unadmitted absolute-host fallback exists')
   absent.append(dict(captured=str(p),absolute_fallback=str(host)))
 keys(d['contexts'],('format','sha256'));need(d['contexts']['format']in ('compiled','text'),'Unknown context format')
 stem=capture/'contexts/file_contexts';actual=Path(str(stem)+'.bin') if d['contexts']['format']=='compiled' else stem
 need({p.name for p in (capture/'contexts').iterdir()}=={actual.name},'Alternate/sidecar contexts not admitted')
 b,identity=read(actual,d['contexts']['sha256'],4*1024**2);snapshots[str(actual)]=identity
 if d['contexts']['format']=='compiled':need(b[:4]==bytes.fromhex('8aff7cf9'),'Compiled context magic missing')
 out=Path(output);need(out.is_absolute() and out.is_relative_to(ROOT/'queries') and not out.exists(),'Fresh owned query output required')
 need(out.parent.resolve().is_relative_to(ROOT),'Output parent escapes fixture');out.mkdir(parents=True)
 f=invoke(ROOT/'bin-r4/resolve_fs_config',[target],out/'fs_config')
 c=invoke(ROOT/'bin-r4/resolve_contexts',[stem],out/'selabel')
 need(f['exit']==0 and c['exit']==0 and not f['stderr']and not c['stderr'],'Native resolver failed or emitted diagnostics; no metadata published')
 fs=f['stdout'].splitlines();labels=c['stdout'].splitlines();need(len(fs)==len(labels)==4,'Partial native stdout')
 rows=[]
 for path,line,label in zip(PATHS,fs,labels):
  m=re.fullmatch(re.escape(path)+r' ([0-9]+) ([0-9]+) ([0-7]{4}) capabilities=(0x[0-9a-f]+)',line)
  l=label.split();need(m is not None and len(l)==2 and l[0]==path,'Unexpected native query output')
  need(re.fullmatch(r'u:object_r:[A-Za-z0-9_]+:s0',l[1])is not None,'Unqualified label form')
  uid,gid,mode,caps=int(m[1]),int(m[2]),int(m[3],8),int(m[4],16);need(caps<2**64,'Capability mask overflow')
  cap=struct.pack('<IIIII',0x02000001,caps&0xffffffff,0,caps>>32,0).hex()if caps else None
  rows.append(dict(path=path,uid=uid,gid=gid,mode=mode,capability_mask=caps,selinux_label=l[1],capability_xattr_v2_hex=cap,zero_capability_means_absence=caps==0))
 for p,identity in snapshots.items():need(snap(Path(p))==identity,'Input identity changed during resolution')
 for a in absent:need(not os.path.lexists(a['captured'])and not os.path.lexists(a['absolute_fallback']),'Absence changed during query')
 result=dict(schema='asus-sdk37-metadata-query-result/v1',scope=d['scope'],binding=d['binding'],input_manifest_sha256=expected,
             tool_group_sha256=d['tool_group_sha256'],native_target_out=d['native_target_out'],captured_target_out=str(target),
             source_bound_capture_query_only=True,production_admission=False,genuine_product_group_claimed=False,
             filesystem_query_exit=f['exit'],selabel_query_exit=c['exit'],files=rows,record_counts=record_counts,
             host_input_identities_before=snapshots,host_input_identities_after={p:snap(Path(p))for p in snapshots},
             explicit_absences=absent,resources=dict(cpus=1,address_space_bytes=1024**3,cpu_seconds=60,wall_seconds=90),
             physical_GO=False)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 bounded();p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True,type=Path);p.add_argument('--pin',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 try:print(json.dumps(query(a.inputs,a.pin,a.output),indent=2));return 0
 except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired)as e:print(json.dumps(dict(state='REFUSED',error=str(e),production_admission=False)));return 2
if __name__=='__main__':raise SystemExit(main())
