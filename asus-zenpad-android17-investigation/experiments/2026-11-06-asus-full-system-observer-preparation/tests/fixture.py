"""One synthetic filesystem; fixture-only expectation documents never enter production."""
from pathlib import Path
import copy
import json
import os
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from admission import (PATHS,FIXTURE,GENUINE,KERNEL_SHA,CONFIG_SHA,identity,sha,canonical,
                       load_group,load_production,need)
from engine import ROOT,TOOLS,bounded,command,environment,generate,execute


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')
    return dict(path=str(path),sha256=sha(path.read_bytes()))


def ref(path):
    return dict(path=str(path),sha256=sha(path.read_bytes()))


def create_fixture():
    f=ROOT/'fixture';f.mkdir();(f/'tmp').mkdir();(f/'target-out').mkdir()
    input_root=f/'input';sizes=[65561,100003,129,513]
    expected_content=[]
    for index,(path,size) in enumerate(zip(PATHS,sizes)):
        p=input_root/path.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True)
        prefix=('FIXTURE_ONLY '+path+'\n').encode()
        data=(prefix+bytes((i*17+index*31)%256 for i in range(size)))[:size]
        p.write_bytes(data);expected_content.append(dict(path=path,bytes=len(data),sha256=sha(data)))
    ctx=f/'fixture-file_contexts'
    ctx.write_text('/ u:object_r:rootfs:s0\n/lost\\+found u:object_r:rootfs:s0\n/system(/.*)? u:object_r:system_file:s0\n/system/build\\.prop u:object_r:system_build_prop:s0\n/system/bin/init u:object_r:init_exec:s0\n/system/bin/run-as u:object_r:runas_exec:s0\n/system/vendor/etc/selinux/vendor_file_contexts u:object_r:vendor_configs_file:s0\n')
    raw=f/'system.raw';raw.touch(exist_ok=False)
    env=environment(f);env['MKE2FS_CONFIG']=str(TOOLS/'sources/mke2fs.conf')
    mk=[str(TOOLS/'bin/mke2fs'),'-O','^has_journal','-L','FIXTURE_ONLY','-I','256','-M','/','-m','0','-t','ext4','-b','4096',str(raw),'8192']
    fill=[str(TOOLS/'bin/e2fsdroid'),'-e','-p',str(f/'target-out'),'-S',str(ctx),'-f',str(input_root),'-a','/',str(raw)]
    for cmd,name in [(mk,'mkfs'),(fill,'e2fsdroid')]:
        result=command(cmd,f/(name+'.log'),env);need(result==dict(exit=0,timed_out=False),name+' failed')
    raw.chmod(0o444)
    fsck=command([str(TOOLS/'bin/e2fsck'),'-f','-n',str(raw)],f/'fsck-before.log',env)
    need(fsck==dict(exit=0,timed_out=False),'Fixture e2fsck failed')
    owner=f/'owner';owner.mkdir()
    # A single filesystem only: complete.json lives beside that same raw via owner directory below.
    # Do not copy the filesystem: place fixture completion beside its original artifact instead.
    complete=write(f/'complete.json',dict(fixture_only=True,fixture_preparation_passed=True,
                                         raw_system=dict(path=str(raw),bytes=raw.stat().st_size,
                                                         sha256=sha(raw.read_bytes()),all_zero_ranges_written=True),
                                         source_system_sha256=sha(raw.read_bytes())))
    capture=f/'public-capture';capture.mkdir();roles={}
    originals=dict(build_image=TOOLS/'sources/build_image.py',mkuserimg=TOOLS/'sources/mkuserimg_mke2fs.py',
                   mke2fs_config=TOOLS/'sources/mke2fs.conf',fs_config_cpp=TOOLS/'sources/fs_config.cpp',
                   platform_file_contexts=ctx,product_file_contexts=ctx)
    for role in ['plan','boardconfig',*originals]:
        p=capture/role
        if role in originals:p.write_bytes(originals[role].read_bytes())
        else:p.write_text(json.dumps({'scope':FIXTURE,'role':role})+'\n')
        roles[role]=dict(path=str(p),sha256=sha(p.read_bytes()),source_path='/FIXTURE_ONLY/'+role)
    source=write(owner/'source-binding.json',dict(schema='asus-fs-source-binding/v1',scope=FIXTURE,
                build_id='fixture-only-r1',sdk=37,capture_root=str(capture),source_roles=roles,
                fs_config_overrides=[],raw_identity=identity(raw.stat()),
                system_image=dict(path=str(raw),sha256=sha(raw.read_bytes()),identity=identity(raw.stat()))))
    phase=write(owner/'fixture-phase.json',dict(scope=FIXTURE,formatter_exit=0,fsck_exit=0,not_a_product_build=True))
    terminal=write(owner/'terminal.json',dict(schema='asus-fixture-terminal/v1',scope=FIXTURE,
                   build_id='fixture-only-r1',fixture_setup_exit_code=0,fixture_fsck_exit_code=0,
                   complete_sha256=complete['sha256'],source_binding_sha256=source['sha256'],sdk=37,
                   native_phase_receipts=[phase]))
    base=dict(scope=FIXTURE,build_id='fixture-only-r1',complete_sha256=complete['sha256'],source_binding_sha256=source['sha256'])
    content=dict(schema='asus-public-content/v1',**base,producer='fixture-known-input-bytes',files=expected_content)
    modes=[0o600,0o755,0o750,0o644];gids=[0,2000,2000,0]
    labels=['system_build_prop','init_exec','runas_exec','vendor_configs_file']
    metadata_rows=[dict(path=path,uid=0,gid=gid,mode=mode,capability_mask=0xc0 if i==2 else 0,
                        selinux_label='u:object_r:'+label+':s0')for i,(path,gid,mode,label) in enumerate(zip(PATHS,gids,modes,labels))]
    resolution=write(owner/'fixture-known-rule-selection.json',dict(scope=FIXTURE,
                     origin='Known synthetic input bytes, captured built-in fs_config selections and explicit fixture contexts; no production resolver or full build claimed',
                     fs_config_source_sha256=roles['fs_config_cpp']['sha256'],rows=metadata_rows,
                     formatter_tool_sha256=sha((TOOLS/'bin/e2fsdroid').read_bytes())))
    metadata=dict(schema='asus-resolved-public-metadata/v1',**base,producer='fixture-known-canned-rules',
                  fs_config_cpp_sha256=roles['fs_config_cpp']['sha256'],product_file_contexts_sha256=roles['product_file_contexts']['sha256'],
                  fs_config_overrides_sha256=sha(canonical([])),
                  resolver_tools=dict(fs_config=sha((TOOLS/'bin/e2fsdroid').read_bytes()),selabel_lookup=sha((TOOLS/'bin/e2fsdroid').read_bytes())),
                  resolution_receipts=[resolution],files=metadata_rows)
    cases={}
    for name in ['positive','wrong-hash','wrong-metadata']:
        c=copy.deepcopy(content);m=copy.deepcopy(metadata)
        if name=='wrong-hash':c['files'][0]['sha256']='0'*64
        if name=='wrong-metadata':m['files'][2]['mode']=0o644
        group=owner/name;group.mkdir()
        content_ref=write(group/'content.json',c);meta_ref=write(group/'metadata.json',m)
        admission=dict(schema='asus-fs-parent-admission/v1',scope=FIXTURE,decision='FIXTURE_TEST_ONLY',
                       build_id='fixture-only-r1',kernel_sha256=KERNEL_SHA,config_sha256=CONFIG_SHA,
                       complete=complete,terminal=terminal,source_binding=source,public_content=content_ref,resolved_metadata=meta_ref)
        a=write(group/'admission.json',admission)
        cases[name]=a
    result=dict(fixture_only=True,raw_path=str(raw),raw_bytes=raw.stat().st_size,raw_sha256=sha(raw.read_bytes()),
                one_filesystem_created=True,cases=cases)
    write(f/'setup-result.json',result);return result


def parser_tests(cases):
    receipts=[]
    for name in ['positive','wrong-hash','wrong-metadata']:
        r=cases[name];a=json.loads(Path(r['path']).read_text());value=load_group(a,r['sha256'],FIXTURE)
        need(value.scope==FIXTURE,'Fixture scope lost')
    def rejected(name,call):
        try:call()
        except (ValueError,KeyError,TypeError,OSError) as e:receipts.append(dict(name=name,rejected=True,error=str(e)))
        else:raise AssertionError(name+' was accepted')
    p=cases['positive'];admission=json.loads(Path(p['path']).read_text())
    rejected('production_rejects_fixture_scope',lambda:load_production(p['path'],p['sha256']))
    rejected('external_parent_pin_required',lambda:load_production(p['path'],'0'*64))
    bad=copy.deepcopy(admission);del bad['source_binding']
    rejected('missing_source_binding',lambda:load_group(bad,'a'*64,FIXTURE))
    # Exercise required per-file boundary checks using new fixture-only receipt revisions.
    for name,mutate in [('missing_hash',lambda d:d['files'][0].pop('sha256')),
                        ('arbitrary_path',lambda d:d['files'][0].update(path='/data/private'))]:
        content=json.loads(Path(admission['public_content']['path']).read_text());mutate(content)
        r=write(ROOT/'fixture/owner'/('rejected-'+name+'.json'),content);a=copy.deepcopy(admission);a['public_content']=r
        rejected(name,lambda a=a:load_group(a,'b'*64,FIXTURE))
    metadata=json.loads(Path(admission['resolved_metadata']['path']).read_text());del metadata['files'][2]['mode']
    a=copy.deepcopy(admission);a['resolved_metadata']=write(ROOT/'fixture/owner/rejected-missing-mode.json',metadata)
    rejected('missing_final_metadata',lambda:load_group(a,'c'*64,FIXTURE))
    metadata=json.loads(Path(admission['resolved_metadata']['path']).read_text());metadata['source_binding_sha256']='0'*64
    a=copy.deepcopy(admission);a['resolved_metadata']=write(ROOT/'fixture/owner/rejected-source-mix.json',metadata)
    rejected('mixed_metadata_source_group',lambda:load_group(a,'d'*64,FIXTURE))
    # Actual default CLI must refuse without emitting any production header.
    env=os.environ.copy();r=command([sys.executable,'-B',str(ROOT/'scripts/full_system.py')],ROOT/'fixture/default-cli-refusal.log',env)
    need(r['exit']==2 and not r['timed_out'],'Default production CLI did not refuse')
    receipts.append(dict(name='default_PLAN_ONLY_absent_admission',rejected=True,exit=2))
    return receipts


def run():
    bounded();setup=create_fixture();parser=parser_tests(setup['cases']);results={}
    for name,ref in setup['cases'].items():
        a=load_group(json.loads(Path(ref['path']).read_text()),ref['sha256'],FIXTURE)
        output=ROOT/'runs'/name;generate(a,output);result=execute(a,output);results[name]=result
        expected=name=='positive'
        need(result['filesystem_observer_passed']==expected,name+' unexpected observer outcome')
        need(result['qemu']==dict(exit=0,timed_out=False),name+' QEMU did not finish')
        need(result['observer_actual_exits']==[('0' if expected else '1',FIXTURE)],'Actual child exit mismatch')
    raw=Path(setup['raw_path']);after=sha(raw.read_bytes());need(after==setup['raw_sha256'],'Synthetic image changed')
    env=environment(ROOT/'fixture');fsck=command([str(TOOLS/'bin/e2fsck'),'-f','-n',str(raw)],ROOT/'fixture/fsck-after.log',env)
    need(fsck==dict(exit=0,timed_out=False),'Final separate host fsck failed')
    result=dict(preparation_qa_passed=True,scope=FIXTURE,actual_product_read_or_mounted=False,
                whole_product_hashes_computed=False,one_synthetic_filesystem=True,fixture_bytes=setup['raw_bytes'],
                fixture_sha256_before=setup['raw_sha256'],fixture_sha256_after=after,
                parser_tests=parser,runtime_results=results,separate_fixture_host_fsck=fsck,
                production_admission_available=False,physical_GO=False,flash_ready=False)
    write(ROOT/'qa-result.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':run()
