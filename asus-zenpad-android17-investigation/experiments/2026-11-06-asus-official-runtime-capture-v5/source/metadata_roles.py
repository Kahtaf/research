"""Fixed SDK37 metadata source roles. Never runs a resolver or admits a product."""
import hashlib,json,os,re,stat,struct
from pathlib import Path
from safeio import need,permitted,load_bytes,sha
GROUP='624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3'
SLOTS=('system','vendor','oem','odm','product','system_ext')
FOUR=('/system/build.prop','/system/bin/init','/system/bin/run-as','/system/vendor/etc/selinux/vendor_file_contexts')
PLAN='attempt/validation/host-metadata-source-plan.json'
PLAN_SCHEMA='asus-sdk37-host-metadata-source-plan/v1'
RECEIPT_SCHEMA='asus-sdk37-installed-four-content/v1'

def keys(value,expected):need(type(value)is dict and set(value)==set(expected),'METADATA_SCHEMA','missing/unknown fields')
def pin(value):need(type(value)is str and re.fullmatch('[a-f0-9]{64}',value),'METADATA_PIN','SHA256');return value
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def normalize_native(value):
    need(type(value)is str and value.startswith('/'),'METADATA_ROOT','absolute native TARGET_OUT')
    if value.endswith('/'):value=value[:-1]
    if value.endswith('/system'):value=value[:-7]
    return value

def validate_override(data):
    offset=0;records=0
    while offset<len(data):
        need(len(data)-offset>=16,'METADATA_OVERRIDE','truncated header')
        length,mode,uid,gid,caps=struct.unpack_from('<HHHHQ',data,offset)
        need(length>16 and length%8==0 and offset+length<=len(data),'METADATA_OVERRIDE','record length')
        prefix=data[offset+16:offset+length];zero=prefix.find(b'\0')
        need(zero>0 and not any(prefix[zero:]) and mode&~0o7777==0,'METADATA_OVERRIDE','prefix/padding/mode')
        prefix[:zero].decode('utf-8');offset+=length;records+=1
    return records

def validate_plan(plan,profile,source_sha):
    keys(plan,('schema','build_id','source_binding_sha256','tool_group_sha256','native_target_out','search_root','search_slots','contexts','installed_content_receipt'))
    need(plan['schema']==PLAN_SCHEMA and plan['build_id']==profile['revision'],'METADATA_BINDING','source plan build')
    need(pin(plan['source_binding_sha256'])==source_sha and pin(plan['tool_group_sha256'])==GROUP,'METADATA_BINDING','source/tool group')
    root=normalize_native(plan['native_target_out'])
    need(root==plan['search_root']==profile['product_out'],'METADATA_ROOT','native origin/search root/profile mismatch')
    need(type(plan['search_slots'])is list and len(plan['search_slots'])==6,'METADATA_SCHEMA','six explicit slots')
    for slot,row in zip(SLOTS,plan['search_slots']):
        keys(row,('slot','state','origin','sha256','absence_attestation_sha256'))
        need(row['slot']==slot and row['origin']==root+'/'+slot+'/etc/fs_config_files','METADATA_SLOT','exact native search slot')
        if row['state']=='present':pin(row['sha256']);need(row['absence_attestation_sha256'] is None,'METADATA_SLOT','present is not absent')
        else:
            need(row['state']=='absent' and row['sha256'] is None,'METADATA_SLOT','explicit absence, never empty replacement')
            attestation={'build_id':profile['revision'],'source_binding_sha256':source_sha,'slot':slot,'origin':row['origin'],'state':'absent'}
            need(pin(row['absence_attestation_sha256'])==sha(encoded(attestation)),'METADATA_ABSENCE','independent source-plan absence binding')
    contexts=plan['contexts'];keys(contexts,('format','origin','sha256'))
    need(contexts['format']=='compiled' and type(contexts['origin'])is str and contexts['origin'].startswith(root+'/') and Path(contexts['origin']).name=='file_contexts.bin','METADATA_CONTEXTS','final compiled contexts only')
    permitted(contexts['origin'][len(profile['aosp'])+1:]);pin(contexts['sha256'])
    receipt=plan['installed_content_receipt'];keys(receipt,('schema','build_id','source_binding_sha256','files'))
    need(receipt['schema']==RECEIPT_SCHEMA and receipt['build_id']==profile['revision'] and receipt['source_binding_sha256']==source_sha,'METADATA_BINDING','installed content source/build')
    need(type(receipt['files'])is list and len(receipt['files'])==4,'METADATA_SCHEMA','exact installed four')
    for path,row in zip(FOUR,receipt['files']):
        keys(row,('path','sha256','bytes'));need(row['path']==path and type(row['bytes'])is int and row['bytes']>=0,'METADATA_CONTENT','fixed path/size');pin(row['sha256'])
    return root

def reference(preparation,expected):
    data=(preparation/'inputs/host-metadata-resolver-reference.json').read_bytes();need(sha(data)==expected,'METADATA_TOOL_REFERENCE','reference pin')
    ref=load_bytes(data);group=(preparation/'inputs/qualified-host-metadata-tools.json').read_bytes();q=load_bytes(group)
    need(sha(group)==GROUP==ref['tool_group_sha256'] and q['tool_only'] is True and q['production_metadata_group'] is False,'METADATA_TOOL_REFERENCE','qualified group, never product admission')
    need(ref['before_copy_after_verified']==147 and ref['canonical_handoff']=='/srv/android/asus-sdk37-host-metadata-resolvers-20261106/handoff-r2','METADATA_TOOL_REFERENCE','canonical accepted scope')
    return {'tool_group_sha256':GROUP,'reference_sha256':expected,'canonical_handoff':ref['canonical_handoff'],'dependency_bytes_revalidated_here':False,'guarded_query_revalidation_required':True}

def absent(state,row,host_exists):
    relative=row['origin'][len(state.profile['aosp'])+1:];permitted(relative)
    try:state.trees['aosp'].stat(relative)
    except FileNotFoundError:pass
    else:need(False,'METADATA_ABSENCE','declared absent native slot exists')
    host='/'+row['slot']+'/etc/fs_config_files'
    need(not host_exists(host),'METADATA_HOST_FALLBACK','absolute host fallback exists')
    return relative

def collect(state,preparation,host_exists=os.path.lexists):
    """Future real capture: called only after terminal() authenticates success."""
    profile=state.profile;need(state.binding['revision']==profile['revision'],'METADATA_BINDING','qualified terminal revision')
    expected=pin(profile.get('host_metadata_source_plan_sha256'))
    row=state.add('kit',PLAN,'host-metadata-source-plan');need(row['kind']=='file' and row['sha256']==expected,'METADATA_BINDING','external source-plan pin')
    validation=load_bytes(state.trees['kit'].read('attempt/validation/complete.json',16*1024**2))
    need(validation.get('host_metadata_source_plan_sha256')==expected,'METADATA_BINDING','qualified validator must bind source plan')
    plan=load_bytes(state.trees['kit'].read(PLAN,4*1024**2));source_sha=state.rows['kit:attempt/validation/source-postimages.json']['sha256']
    validate_plan(plan,profile,source_sha)
    installed=plan['installed_content_receipt'];content_sha=sha(encoded(installed))
    need(validation.get('installed_four_content_receipt_sha256')==content_sha,'METADATA_BINDING','qualified validator installed-four receipt')
    for entry in installed['files']:
        path=profile['product_out'][len(profile['aosp'])+1:]+entry['path']
        observed=state.add('aosp',path,'host-metadata-installed-four')
        need(observed['kind']=='file' and observed['sha256']==entry['sha256'] and observed['bytes']==entry['bytes'],'METADATA_CONTENT',entry['path'])
    slots=[]
    for spec in plan['search_slots']:
        result=dict(spec,captured_path='layout/'+spec['slot']+'/etc/fs_config_files')
        if spec['state']=='absent':
            result.update(source_relative=absent(state,spec,host_exists),bytes=None,record_count=None,absolute_host_fallback_absent=True)
        else:
            path=spec['origin'][len(profile['aosp'])+1:];permitted(path)
            data=state.trees['aosp'].read(path,1024**2,allow_empty=True);count=validate_override(data)
            observed=state.add('aosp',path,'host-metadata-fs-config-files',allow_empty=True)
            need(observed['kind']=='file' and observed['sha256']==spec['sha256']==sha(data),'METADATA_CONTENT',path)
            result.update(source_relative=path,bytes=len(data),record_count=count,absolute_host_fallback_absent=None)
        slots.append(result)
    contexts=plan['contexts'];path=contexts['origin'][len(profile['aosp'])+1:]
    data=state.trees['aosp'].read(path,4*1024**2)
    need(data[:4]==bytes.fromhex('8aff7cf9'),'METADATA_CONTEXTS','compiled header; native load still required')
    observed=state.add('aosp',path,'host-metadata-final-compiled-contexts')
    need(observed['kind']=='file' and observed['sha256']==contexts['sha256']==sha(data),'METADATA_CONTEXTS','final binary pin')
    return {'schema':'asus-sdk37-authenticated-metadata-source-roles/v1','binding':{'build_id':profile['revision'],'complete_sha256':state.rows['kit:attempt/validation/complete.json']['sha256'],'source_binding_sha256':source_sha,'installed_content_receipt_sha256':content_sha},'tool_reference':reference(preparation,state.selector['host_metadata_reference_sha256']),'native_source_plan_sha256':expected,'native_target_out':plan['native_target_out'],'search_root':plan['search_root'],'search_slots':slots,'contexts':dict(contexts,source_relative=path,bytes=len(data),captured_path='contexts/file_contexts.bin'),'installed_content_receipt':installed,'query_layout_materialized':False,'native_query_executed':False,'native_metadata_admitted':False,'production_admission':False}

def recheck(state,roles,host_exists=os.path.lexists):
    for row in roles['search_slots']:
        if row['state']=='absent':absent(state,row,host_exists)
