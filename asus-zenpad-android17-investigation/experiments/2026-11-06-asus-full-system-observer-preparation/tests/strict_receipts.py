"""Refine receipt-contract QA without creating another filesystem or overwriting a run."""
from pathlib import Path
import copy,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from admission import *
from engine import ROOT,bounded,generate,execute,command


def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as out:out.write(json.dumps(obj,indent=2)+'\n')
    return dict(path=str(p),sha256=sha(p.read_bytes()))


def run():
    bounded();base=ROOT/'fixture/owner/strict-r2';base.mkdir();cases={};receipts=[]
    for name in ['positive','wrong-hash','wrong-metadata']:
        original=ROOT/'fixture/owner'/name/'admission.json';a=json.loads(original.read_text())
        metadata=json.loads(Path(a['resolved_metadata']['path']).read_text())
        # Resolution is independently fixed to the actual selected fixture metadata. The metadata-negative
        # case changes expected mode in both fixture-only documents to test the guest, not the parser.
        d=base/name;d.mkdir();rows=metadata['files']
        fsc=d/'known-fixture-fs-config.txt';fsc.write_text(''.join(r['path']+' '+str(r['uid'])+' '+str(r['gid'])+' '+format(r['mode'],'04o')+' capabilities='+hex(r['capability_mask'])+'\n'for r in rows))
        lab=d/'known-fixture-selabel.txt';lab.write_text(''.join(r['path']+' '+r['selinux_label']+'\n'for r in rows))
        common={k:metadata[k]for k in ('scope','build_id','complete_sha256','source_binding_sha256','fs_config_cpp_sha256',
                                      'product_file_contexts_sha256','fs_config_overrides_sha256','resolver_tools','files')}
        resolution=write(d/'resolution.json',dict(schema='asus-fixture-known-resolution/v1',**common,
                         fixture_formatter_exit_code=0,stdout=dict(fs_config=dict(path=str(fsc),sha256=sha(fsc.read_bytes())),
                         selabel_lookup=dict(path=str(lab),sha256=sha(lab.read_bytes())))))
        metadata['resolution_receipts']=[resolution];a['resolved_metadata']=write(d/'metadata.json',metadata)
        ar=write(d/'admission.json',a);admitted=load_group(a,ar['sha256'],FIXTURE);cases[name]=ar
        out=ROOT/'runs'/('strict-'+name);generate(admitted,out);result=execute(admitted,out)
        expected=name=='positive';need(result['filesystem_observer_passed']==expected,'Strict '+name+' outcome')
        need(result['observer_actual_exits']==[('0'if expected else'1',FIXTURE)],'Actual exit mismatch')
        receipts.append(dict(case=name,generation=str(out/'generation.json'),result=result))
    def reject(name,call):
        try:call()
        except (ValueError,KeyError,TypeError,OSError) as e:return dict(case=name,rejected=True,error=str(e))
        raise AssertionError(name+' accepted')
    positive=cases['positive'];a=json.loads(Path(positive['path']).read_text());m=json.loads(Path(a['resolved_metadata']['path']).read_text())
    parser=[reject('production_rejects_fixture',lambda:load_production(positive['path'],positive['sha256']))]
    for name,mutate in [('missing_hash',lambda c:c['files'][0].pop('sha256')),
                        ('arbitrary_path',lambda c:c['files'][0].update(path='/data/private'))]:
        c=json.loads(Path(a['public_content']['path']).read_text());mutate(c);b=copy.deepcopy(a);b['public_content']=write(base/(name+'.json'),c)
        parser.append(reject(name,lambda b=b:load_group(b,'a'*64,FIXTURE)))
    for name,mutate in [('missing_final_mode',lambda m:m['files'][2].pop('mode')),
                        ('missing_resolution',lambda m:m.update(resolution_receipts=[])),
                        ('resolution_value_mismatch',lambda m:m['files'][2].update(mode=0o600)),
                        ('mixed_source_group',lambda m:m.update(source_binding_sha256='0'*64))]:
        changed=copy.deepcopy(m);mutate(changed);b=copy.deepcopy(a);b['resolved_metadata']=write(base/(name+'.json'),changed)
        parser.append(reject(name,lambda b=b:load_group(b,'b'*64,FIXTURE)))
    b=copy.deepcopy(a);b['scope']=GENUINE;b['decision']='ACCEPT_COHERENT_PRODUCT_INPUTS'
    r=write(base/'attempted-promotion.json',b)
    parser.append(reject('retagged_fixture_cannot_promote',lambda:load_production(r['path'],r['sha256'])))
    parser.append(reject('wrong_external_admission_pin',lambda:load_production(positive['path'],'0'*64)))
    # Verify default and explicit GENERATE/EXECUTE refusals emit no header for a fixture admission.
    cli=[]
    for mode in ['PLAN_ONLY','GENERATE','EXECUTE']:
        out=ROOT/'runs'/('refused-'+mode)
        cmd=[sys.executable,'-B',str(ROOT/'scripts/full_system.py'),'--mode',mode,'--admission',positive['path'],
             '--admission-pin',positive['sha256'],'--output',str(out)]
        terminal=command(cmd,base/('cli-'+mode+'.log'),None)
        need(terminal==dict(exit=2,timed_out=False) and not out.exists(),'CLI emitted synthetic production input')
        cli.append(dict(mode=mode,terminal=terminal,output_created=False))
    result=dict(strict_qa_passed=True,scope=FIXTURE,cases=cases,runs=receipts,parser_rejections=parser,
                production_cli_refusals=cli,actual_product_read_or_mounted=False,physical_GO=False)
    write(ROOT/'strict-qa-result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
