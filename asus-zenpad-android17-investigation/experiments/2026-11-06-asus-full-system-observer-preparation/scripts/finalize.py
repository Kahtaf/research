"""Local evidence verification only; does not contact the builder or execute a guest."""
from pathlib import Path
import ast,hashlib,json,re,datetime
S=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((S/'evidence'/n).read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
audit=load('audit.json');strict=load('strict-qa-result.json');final=load('final-capture.json');parser=load('final-parser-qa.json');seal=load('immutable-seal.json');setup=load('setup.json')
assert audit['audit_passed'] and strict['strict_qa_passed'] and final['final_capture_passed'] and parser['final_parser_qa_passed']
assert seal['owned_immutable_inputs_sealed'] and seal['files']==setup['copied_files']==2368 and seal['all_content_pins_match']
assert audit['immutable_pins_sha256']==setup['immutable_pins_sha256']==final['immutable_pins_sha256']
assert audit['tool_copy_receipts_sha256']==setup['copy_receipts_sha256']==final['copy_receipts_sha256']
assert audit['separate_final_host_fsck']==dict(exit=0,timed_out=False)
assert audit['publisher_refused_fixture']==dict(exit=2,timed_out=False)
for name,pin in final['current_source_pins'].items():assert sha(S/name)==pin,name+' source drift'
summary={}
for row in strict['runs']:
 name=row['case'];run=row['result'];log=audit['logs']['strict-'+name]['serial.log'];expected=name=='positive'
 assert run['filesystem_observer_passed'] is expected and run['qemu']==dict(exit=0,timed_out=False)
 assert run['identities_unchanged'] and not run['kernel_errors'] and run['scope']=='FIXTURE_ONLY'
 expected_exit='0' if expected else '1'
 assert re.findall(r'^FULL_SYSTEM_FS_EXIT status=([0-9]+) scope=FIXTURE_ONLY\r?$',log,re.M)==[expected_exit]
 assert re.findall(r'^FULL_SYSTEM_FS_RESULT failures=([0-9]+) scope=FIXTURE_ONLY\r?$',log,re.M)==[expected_exit]
 assert len(re.findall(r'^FILE /system/',log,re.M))==4
 failed=re.findall(r'^CHECK (\S+) FAIL',log,re.M)
 assert failed==([] if expected else ['stream_eof_exact_size_sha256' if name=='wrong-hash' else 'regular_uid_gid_mode_size'])
 assert 'CHECK clean_unmount PASS' in log and 'CHECK existing_file_write_denied_EROFS PASS' in log
 gen=json.loads(audit['logs']['strict-'+name]['generation.json'])
 assert gen['generated']['observer.c']==sha(S/'source/observer.c') and gen['generated']['sha256.h']==sha(S/'source/sha256.h')
 summary[name]=dict(observer_failures=int(expected_exit),observer_actual_exit=int(expected_exit),qemu_exit=0,
                    expected_outcome_verified=True,failed_checks=failed,generated_pins=gen['generated'],
                    remote_run=final['remote_root']+'/runs/strict-'+name)
for item in strict['parser_rejections']:assert item['rejected']
for item in strict['production_cli_refusals']:assert item['terminal']==dict(exit=2,timed_out=False)and not item['output_created']
assert final['host_fsck_cli_refused_fixture']==dict(exit=2,timed_out=False)
old=S.parent/'2026-11-06-asus-sdk37-system-ext4-qualification';old_manifest=json.loads((old/'artifact-manifest.json').read_text())
for name,row in old_manifest.items():assert sha(old/name)==row['sha256'],'Prior mechanism artifact changed: '+name
assert sha(old/'evidence/parent-scoped-acceptance.json')==sha(S/'evidence/mechanism-parent-acceptance.json')
for p in list((S/'scripts').glob('*.py'))+list((S/'tests').glob('*.py')):ast.parse(p.read_text())
result=dict(schema_version=1,decision='PREPARATION_COMPLETE_FIXTURE_QA_PASS_GENUINE_INPUTS_PENDING',
            scope='Preparation and synthetic fixture tests only',remote_root=final['remote_root'],
            kernel_sha256='c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080',
            config_sha256='0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f',
            source_pins=final['current_source_pins'],immutable_pins_sha256=final['immutable_pins_sha256'],
            before_copy_after_verified_files=2368,prior_mechanism_local_payloads_unchanged=len(old_manifest),
            specimen=dict(bytes=33554432,sha256=audit['fixture_final_sha256'],filesystems_created=1),
            accepted_fixture_runs=summary,parser_rejections_verified=len(strict['parser_rejections']),
            production_modes_refuse_fixture=True,default_without_admission_refuses=True,
            production_expectation_publisher_refuses_fixture=True,host_fsck_cli_refuses_fixture=True,
            final_separate_fixture_e2fsck_exit=0,
            genuine_input_group_available=False,production_header_emitted=False,actual_product_read_or_mounted=False,
            real_host_metadata_resolvers_built_or_executed=False,whole_product_image_copied_or_rehashed=False,
            full_SYSTEM_accepted=False,android_runtime_qualified=False,physical_GO=False,flash_ready=False,
            missing_contracts=['Successful later parent complete.json + pinned native/host terminal binding',
                               'Exact coherent public source/generated-rule/properties/installed-content capture',
                               'Genuine SDK37 fs_config/selabel helper build+exit+stdout receipts with actual overrides/contexts',
                               'Externally reviewed and pinned final parent admission'],
            future_commands='PARENT-COMMANDS.md',receipt_contract='contracts/receipt-contract.md')
dump(S/'acceptance.json',result)
print(json.dumps({'decision':result['decision'],'prior_payloads_unchanged':len(old_manifest),
                  'observer_source_sha256':result['source_pins']['source/observer.c'],
                  'runtime_controls_verified':list(summary),'parser_rejections_verified':len(strict['parser_rejections'])},indent=2))
