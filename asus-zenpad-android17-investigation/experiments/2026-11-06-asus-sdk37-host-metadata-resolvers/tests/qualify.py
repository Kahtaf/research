from pathlib import Path
import copy,json,os,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from query import *


def save(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def record(path,uid,gid,mode,caps):
 p=path.encode()+b'\0';size=(16+len(p)+7)//8*8;return struct.pack('<HHHHQ',size,mode,uid,gid,caps)+p+bytes(size-16-len(p))

def fixture(root):
 for slot in SLOTS:
  p=root/'layout'/slot/'etc';p.mkdir(parents=True);(p/'fs_config_files').write_bytes(b'')
 (root/'contexts').mkdir();labels=['fixture_build_prop','fixture_init','fixture_runas','fixture_vendor_contexts']
 text=''.join(path.replace('.','\\.')+' -- u:object_r:'+label+':s0\n'for path,label in zip(PATHS,labels));(root/'contexts/file_contexts').write_text(text)
 return labels

def manifest(root,fmt='text'):
 return dict(schema='asus-sdk37-metadata-query-inputs/v1',scope='FIXTURE_ONLY',binding=dict(fixture_id=root.name),
             capture_root=str(root),native_target_out='/FIXTURE_ONLY/product/system',
             search_slots=[dict(slot=s,state='present',sha256=sha((root/'layout'/s/'etc/fs_config_files').read_bytes()))for s in SLOTS],
             contexts=dict(format=fmt,sha256=sha((root/'contexts'/('file_contexts.bin'if fmt=='compiled'else'file_contexts')).read_bytes())),
             tool_group_sha256=sha((ROOT/'qualified-tools.json').read_bytes()))

def run():
 bounded();F=ROOT/'fixtures';F.mkdir();(ROOT/'queries').mkdir();logs=ROOT/'qa-logs';logs.mkdir();allresults={};checks=[]
 def native(name,tool,args):
  r=invoke(tool,args,logs/name);allresults[name]=r;return r
 def expect(name,ok):need(ok,name+' failed');checks.append(name)
 base=F/'baseline';base.mkdir();fixture(base)
 baseline=native('builtin_defaults',ROOT/'bin-r4/resolve_fs_config',[base/'layout/system'])
 expect('builtin-defaults-source-match',baseline['exit']==0 and baseline['stdout'].splitlines()==[
 PATHS[0]+' 0 0 0600 capabilities=0x0',PATHS[1]+' 0 2000 0755 capabilities=0x0',PATHS[2]+' 0 2000 0750 capabilities=0xc0',PATHS[3]+' 0 0 0644 capabilities=0x0'])
 custom=F/'custom';custom.mkdir();labels=fixture(custom)
 (custom/'layout/system/etc/fs_config_files').write_bytes(record('system/build.prop',1101,2101,0o640,0)+record('system/bin/init',1102,2102,0o750,0x400))
 (custom/'layout/vendor/etc/fs_config_files').write_bytes(record('system/bin/run-as',1103,2103,0o710,(1<<39)|0xc0)+record('vendor/etc/selinux/vendor_file_contexts',1104,2104,0o440,0))
 c=native('actual_override_consumption',ROOT/'bin-r4/resolve_fs_config',[custom/'layout/system'])
 expected=[PATHS[0]+' 1101 2101 0640 capabilities=0x0',PATHS[1]+' 1102 2102 0750 capabilities=0x400',PATHS[2]+' 1103 2103 0710 capabilities=0x80000000c0',PATHS[3]+' 1104 2104 0440 capabilities=0x0']
 expect('override-files-and-system-vendor-alias-consumed',c['exit']==0 and c['stdout'].splitlines()==expected)
 for spelling in [str(custom/'layout'),str(custom/'layout/system')+'/']:
  r=native('target-spelling-'+str(len(allresults)),ROOT/'bin-r4/resolve_fs_config',[spelling]);expect('TARGET_OUT-normalisation-'+spelling,r['stdout']==c['stdout']and r['exit']==0)
 text=native('text_contexts',ROOT/'bin-r4/resolve_contexts',[custom/'contexts/file_contexts'])
 expect('text-labels-exact',text['exit']==0 and text['stdout'].splitlines()==[p+' u:object_r:'+l+':s0'for p,l in zip(PATHS,labels)])
 compiled=native('compile_contexts',I/'bin/sefcontext_compile',['-o',custom/'contexts/file_contexts.bin',custom/'contexts/file_contexts']);expect('SDK37-context-compiler-exit',compiled['exit']==0)
 # Remove neither original: capture separate compiled-only fixture directory to prevent alt fallback.
 import shutil
 binary=F/'compiled-only';shutil.copytree(custom,binary);(binary/'contexts/file_contexts').unlink()
 r=native('compiled_only_stem',ROOT/'bin-r4/resolve_contexts',[binary/'contexts/file_contexts']);expect('compiled-only-stem-exact',r['exit']==0 and r['stdout']==text['stdout'])
 r=native('compiled_direct_filename',ROOT/'bin-r4/resolve_contexts',[binary/'contexts/file_contexts.bin']);expect('compiled-direct-filename-exact',r['exit']==0 and r['stdout']==text['stdout'])
 m=manifest(binary,'compiled');mp=F/'positive-inputs.json';save(mp,m)
 positive=query(mp,sha(mp.read_bytes()),ROOT/'queries/positive')
 expect('strict-positive-four-rows',len(positive['files'])==4)
 expect('zero-capability-explicit-absence',positive['files'][0]['capability_xattr_v2_hex']is None and positive['files'][3]['capability_xattr_v2_hex']is None)
 expect('revision2-high-word-roundtrip',positive['files'][2]['capability_xattr_v2_hex']==struct.pack('<IIIII',0x02000001,0xc0,0,0x80,0).hex())
 def guard_reject(name,root,mutate=None,fmt='text'):
  m=manifest(root,fmt)
  if mutate:mutate(m)
  p=F/(name+'-inputs.json');save(p,m)
  try:query(p,sha(p.read_bytes()),ROOT/'queries'/name)
  except (ValueError,KeyError,OSError,TypeError)as e:allresults['guard-'+name]=dict(refused=True,error=str(e));checks.append('guard-refused-'+name)
  else:raise AssertionError(name+' guard accepted')
 # Wrong valid override is observable natively; the externally fixed old hash rejects its substitution.
 wrong=F/'wrong-override';shutil.copytree(binary,wrong)
 (wrong/'layout/vendor/etc/fs_config_files').write_bytes(record('system/bin/run-as',3333,4444,0o600,0))
 r=native('wrong_valid_override',ROOT/'bin-r4/resolve_fs_config',[wrong/'layout/system']);expect('wrong-valid-data-is-not-success-equivalence',r['exit']==0 and r['stdout']!=c['stdout'])
 guard_reject('wrong-override-pin',wrong,lambda m:m['search_slots'][1].update(sha256=sha((binary/'layout/vendor/etc/fs_config_files').read_bytes())),fmt='compiled')
 missing=F/'missing-override';shutil.copytree(binary,missing);(missing/'layout/vendor/etc/fs_config_files').unlink()
 r=native('missing_override_native_fallback',ROOT/'bin-r4/resolve_fs_config',[missing/'layout/system']);expect('missing-override-library-fallback-exit0',r['exit']==0 and PATHS[2]+' 0 2000 0750 capabilities=0xc0' in r['stdout'])
 badm=copy.deepcopy(m);badm['capture_root']=str(missing);p=F/'missing-override-inputs.json';save(p,badm)
 try:query(p,sha(p.read_bytes()),ROOT/'queries/missing-override')
 except (ValueError,OSError)as e:allresults['guard-missing-override']=dict(refused=True,error=str(e));checks.append('guard-refused-missing-override')
 else:raise AssertionError('Missing override admitted')
 malformed=F/'malformed-override';shutil.copytree(binary,malformed);(malformed/'layout/vendor/etc/fs_config_files').write_bytes(struct.pack('<HHHHQ',16,0o600,999,999,0))
 r=native('malformed_override_native_fallback',ROOT/'bin-r4/resolve_fs_config',[malformed/'layout/system']);expect('malformed-override-logged-fallback-exit0',r['exit']==0 and 'len too short' in r['stderr'])
 guard_reject('malformed-override',malformed,fmt='compiled')
 r=native('wrong_root_native_fallback',ROOT/'bin-r4/resolve_fs_config',[base/'layout/system']);expect('wrong-root-is-source-defaults',r['stdout']==baseline['stdout'])
 wrongroot=copy.deepcopy(m);wrongroot['capture_root']=str(base);p=F/'wrong-root-inputs.json';save(p,wrongroot)
 try:query(p,sha(p.read_bytes()),ROOT/'queries/wrong-root')
 except (ValueError,OSError)as e:allresults['guard-wrong-root']=dict(refused=True,error=str(e));checks.append('guard-refused-wrong-root')
 else:raise AssertionError('Wrong root admitted')
 # Context missing/malformed cases return no partial stdout with corrected atomic TU.
 r=native('missing_contexts',ROOT/'bin-r4/resolve_contexts',[F/'nonexistent/file_contexts']);expect('missing-context-exit1-empty-stdout',r['exit']==1 and not r['stdout'])
 badctx=F/'malformed-context';shutil.copytree(base,badctx);(badctx/'contexts/file_contexts').write_text('[ -- u:object_r:broken:s0\n')
 r=native('malformed_contexts',ROOT/'bin-r4/resolve_contexts',[badctx/'contexts/file_contexts']);expect('malformed-context-exit1-empty-stdout',r['exit']==1 and not r['stdout'])
 guard_reject('malformed-context',badctx)
 corrupt=F/'corrupt-binary';shutil.copytree(binary,corrupt);(corrupt/'contexts/file_contexts.bin').write_bytes((binary/'contexts/file_contexts.bin').read_bytes()[:12])
 r=native('corrupt_compiled_only',ROOT/'bin-r4/resolve_contexts',[corrupt/'contexts/file_contexts']);expect('corrupt-binary-exit1-no-alternate',r['exit']==1 and not r['stdout'])
 guard_reject('corrupt-binary',corrupt,fmt='compiled')
 alternate=F/'corrupt-with-text-fallback';shutil.copytree(custom,alternate);(alternate/'contexts/file_contexts.bin').write_bytes((binary/'contexts/file_contexts.bin').read_bytes()[:12]);os.utime(alternate/'contexts/file_contexts.bin',(1900000000,1900000000))
 r=native('corrupt_binary_text_fallback',ROOT/'bin-r4/resolve_contexts',[alternate/'contexts/file_contexts']);expect('corrupt-bin-can-be-masked-by-genuine-text-fallback',r['exit']==0 and r['stdout']==text['stdout'])
 guard_reject('unadmitted-alternate-context',alternate,fmt='compiled')
 partial=F/'missing-fourth-label';shutil.copytree(base,partial);(partial/'contexts/file_contexts').write_text('\n'.join((base/'contexts/file_contexts').read_text().splitlines()[:3])+'\n')
 r=native('fourth_label_missing',ROOT/'bin-r4/resolve_contexts',[partial/'contexts/file_contexts']);expect('atomic-no-partial-label-stdout',r['exit']==1 and not r['stdout'])
 # HOST+BASEONLY ignore local substitutions, but the query guard refuses unadmitted sidecars.
 side=F/'sidecar';shutil.copytree(binary,side);(side/'contexts/file_contexts.local').write_text('/system/bin/run-as -- u:object_r:sidecar_wrong:s0\n');(side/'contexts/file_contexts.subs').write_text('/system /not_system\n')
 r=native('host_baseonly_sidecars_ignored',ROOT/'bin-r4/resolve_contexts',[side/'contexts/file_contexts']);expect('HOST-baseonly-ignores-sidecars',r['exit']==0 and r['stdout']==text['stdout'])
 guard_reject('sidecar',side,fmt='compiled')
 result=dict(qualified=True,scope='FIXTURE_ONLY',checks=checks,native_and_guard_receipts=allresults,positive_query=positive,
             actual_product_selected_or_captured=False,actual_SYSTEM_read_or_mounted=False,production_metadata_claimed=False,
             physical_GO=False)
 save(ROOT/'qa.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
