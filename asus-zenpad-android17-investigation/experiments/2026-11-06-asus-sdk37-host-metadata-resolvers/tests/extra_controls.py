from pathlib import Path
import json,os,shutil,struct,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from query import *

def run():
 bounded();F=ROOT/'fixtures';logs=ROOT/'qa-extra';logs.mkdir();checks={};binary=F/'compiled-only';base=F/'baseline'
 absent=F/'explicit-absent';shutil.copytree(binary,absent);(absent/'layout/oem/etc/fs_config_files').unlink()
 original=json.loads((F/'positive-inputs.json').read_text());m=json.loads(json.dumps(original));m['capture_root']=str(absent);m['binding']['fixture_id']='explicit-absence';m['search_slots'][2].update(state='absent',sha256=None)
 p=F/'explicit-absence-inputs.json';p.write_text(json.dumps(m,indent=2)+'\n')
 q=query(p,sha(p.read_bytes()),ROOT/'queries/explicit-absence');need(len(q['explicit_absences'])==1,'Explicit absence not checked');checks['explicit_absence_success']=q
 wrong=F/'wrong-valid-context';shutil.copytree(base,wrong);pctx=wrong/'contexts/file_contexts';oldpin=sha(pctx.read_bytes());pctx.write_text(pctx.read_text().replace('fixture_runas','wrong_valid_runas'))
 r=invoke(ROOT/'bin-r4/resolve_contexts',[pctx],logs/'wrong-valid-context');need(r['exit']==0 and 'wrong_valid_runas' in r['stdout'],'Wrong context not observed');checks['wrong_valid_context_native']=r
 m=json.loads(json.dumps(original));m['capture_root']=str(wrong);m['search_slots']=[dict(slot=s,state='present',sha256=sha((wrong/'layout'/s/'etc/fs_config_files').read_bytes()))for s in SLOTS];m['contexts']=dict(format='text',sha256=oldpin)
 p=F/'wrong-context-inputs.json';p.write_text(json.dumps(m,indent=2)+'\n')
 try:query(p,sha(p.read_bytes()),ROOT/'queries/wrong-context')
 except ValueError as e:checks['wrong_context_guard']=dict(refused=True,error=str(e))
 else:raise AssertionError('Wrong context admitted')
 priority=F/'search-priority';shutil.copytree(binary,priority);prefix=b'system/bin/run-as\0';length=(16+len(prefix)+7)//8*8
 with (priority/'layout/system/etc/fs_config_files').open('ab')as f:f.write(struct.pack('<HHHHQ',length,0o700,1203,2203,0)+prefix+bytes(length-16-len(prefix)))
 r=invoke(ROOT/'bin-r4/resolve_fs_config',[priority/'layout/system'],logs/'system-precedes-vendor');need(PATHS[2]+' 1203 2203 0700 capabilities=0x0' in r['stdout'],'Search priority wrong');checks['system_search_priority']=r
 # Real command-line path and refusal statuses, in addition to direct library calls.
 for name,pinvalue,expected_exit in [('positive',sha((F/'positive-inputs.json').read_bytes()),0),('wrong-pin','0'*64,2)]:
  out=ROOT/'queries'/('cli-'+name);cmd=[sys.executable,'-B',str(ROOT/'scripts/query.py'),'--inputs',str(F/'positive-inputs.json'),'--pin',pinvalue,'--output',str(out)]
  r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90,preexec_fn=bounded);need(r.returncode==expected_exit,'CLI exit mismatch')
  if expected_exit:need(not out.exists(),'Refusal created output')
  checks['cli-'+name]=dict(argv=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr,output_created=out.exists())
 result=dict(extra_controls_passed=True,checks=checks,actual_product_accessed=False,production_admission=False)
 (ROOT/'extra-qa.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':run()
