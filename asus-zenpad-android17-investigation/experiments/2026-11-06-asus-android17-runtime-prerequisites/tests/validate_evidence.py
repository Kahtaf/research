#!/usr/bin/env python3
"""Validate captured runtime outcomes and boundaries, not source-shaped mocks."""
from pathlib import Path
import hashlib,json,re,sys
R=Path(__file__).resolve().parents[1]; E=R/'evidence'; run=sys.argv[1] if len(sys.argv)>1 else 'run-r5'
r=json.loads((E/run/'result.json').read_text());log=(E/run/'serial.log').read_text()
assert r['qemu_returncode']==0 and not r['timed_out'] and r['complete']
assert r['guest']['failures']==0 and r['passed']
assert r['all_material_hashes_pass'] and len(r['material_hashes'])==68
assert all(x['actual']==x['expected'] and x['passed'] for x in r['material_hashes'])
assert r['binder_pass'] and r['corruption_detected']
assert not r['full_apex_activation'] and not r['physical_hardware_validated']
assert 'ext4_data_mount rc=0' in log and '/dev/vda /data ext4 rw,' in log
loops=re.findall(r'LOOP_READY index=(\d+) flags=(\d+).*direct=(\d+)',log)
assert len(loops)==3 and all(x[2]=='1' for x in loops)
assert log.count('LOOP_CONFIGURE_PROBE rc=-1 errno=9 supported=1')==3
assert log.count('CHECK LOOP_CONFIGURE rc=0')==3
assert log.count('CHECK erofs_bare_mount rc=0')==2
assert log.count('CHECK erofs_verity_mount rc=0')==2
assert 'VERITY_CORRUPTION_READ bytes=-1 errno=5 expected_EIO=1' in log
assert len(set(re.findall(r'BINDER_CLIENT_THREAD tid=(\d+)',log)))==4
assert len(set(re.findall(r'BINDER_SERVICE_THREAD tid=(\d+)',log)))>=2
b=json.loads(re.search(r'BINDER_RESULT (\{[^\n]+\})',log)[1]);assert b=={'threads':4,'sync_replies':200,'oneway_sent':20,'server_calls':220,'client_deaths':1,'failures':0}
assert 'BINDER_CONTEXT_MANAGER ok=1' in log
assert 'spam_rc=-22 freeze_rc=-22' in log and 'BINDER_FREEZE_INFO rc=-22' in log
assert 'BINDER_EXIT death_client=0 multithread_client=0' in log
assert log.count('VERITY_ACTIVE_TABLE name=')==3 and log.count('check_at_most_once')==3
c=json.loads((E/'config-expanded-comparison-r4.json').read_text());assert all(x['equal'] for x in c.values())
s=json.loads((E/'full-source-equivalence.json').read_text());assert s['all_other_kernel_files_equal'] and s['only_difference']==['drivers/irqchip/irq-gic-v3.c']
for n in ['adbd','google']:
 assert 'Successfully verified sha256 hashtree' in (E/(n+'-avb-verify.txt')).read_text()
cmd=json.loads((E/run/'qemu-command.json').read_text());assert cmd[cmd.index('-smp')+1]=='2' and int(cmd[cmd.index('-m')+1])<=2048 and cmd[cmd.index('-nic')+1]=='none'
assert not any('usb-host' in a for a in cmd)
total=0
for filename,old_source in [('capture-manifest.json',True),('capture-manifest-r2.json',False)]:
 manifest=json.loads((R/'artifacts'/filename).read_text())
 for f in manifest:
  p=(R/'artifacts/captured-source'/f['path'][7:]) if old_source and f['path'].startswith('source/') else R/f['path']
  assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],str(p)
 total+=len(manifest)
assert int((E/run/'runner.exit').read_text())==0
assert r['kernel_sha256'] in (E/'kernel-r4.sha256').read_text()
print(json.dumps({'passed':True,'material_reads':68,'payloads':2,'source_equivalent_files':len(s['selected_files']),'matching_config_values':len(c),'binder_threads':4,'binder_sync_replies':200,'binder_oneway_calls':20,'client_deaths':1,'captured_manifest_entries_verified':total},indent=2))
