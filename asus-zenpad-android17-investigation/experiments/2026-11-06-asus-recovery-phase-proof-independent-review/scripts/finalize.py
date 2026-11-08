from pathlib import Path
import json,re,hashlib,subprocess
R=Path(__file__).resolve().parents[1];E=R/'fixture/evidence'
for name in ['independent','independent-policy','independent-clean-policy']:
 assert (R/'evidence'/f'{name}.exit').read_text().strip()=='0'
checks={}
for name,expected in [('linux-sessions-after',23),('linux-sessions-before',23),('linux-guard',1),('linux-handoff',1),('review-boundaries',8),('review-exec',1)]:
 log=(E/f'{name}.stderr').read_text();assert log.rstrip().endswith('OK'),log
 n=int(re.search(r'Ran (\d+) test',log)[1]);assert n==expected;checks[name]=dict(passed=True,methods=n)
assert (E/'policy-reachability.txt').read_bytes()==(R/'snapshot/evidence/policy-reachability.txt').read_bytes()
assert 'independent policy assertions passed' in (E/'review-policy.stdout').read_text()
for name,want in [('linux-cpus.txt','0'),('linux-cpu-quota.txt','100000 100000'),('linux-memory-limit.txt','1073741824')]:assert (E/name).read_text().strip()==want
peaks={n:int((E/n).read_text()) for n in ['review-memory-peak.txt','review-policy-memory-peak.txt']}
assert max(peaks.values())<1024**3
counts=json.loads((E/'full-geometry-counts.json').read_text());assert counts['totals']['before']['recovery_bytes']-counts['totals']['after']['recovery_bytes']==241111289856
assert 14403*16740352==241111289856
assert (R/'fixture/source/rescue.c').read_bytes()==(R/'snapshot/source/rescue.c').read_bytes()
assert (R/'fixture/source/recovery_phase.h').read_bytes()==(R/'snapshot/source/recovery_phase.h').read_bytes()
subprocess.run(['python3',str(R/'scripts/verify_inputs.py')],check=True)
v=dict(passed=True,tests=checks,total_test_methods=sum(c['methods'] for c in checks.values()),production_body_bytes_unchanged=True,effective_policy_rows=144,effective_policy_matches_original=True,independent_policy_clean_rebuild=True,all_six_actors_nonpermissive=True,daemon_helper_self_attributes_only=True,daemon_helper_extended_ioctl='BLKGETSIZE64 only; four node grants each',new_witnesses=['same-node O_RDWR dup2 substitution accepted outside production flow','persistent same-node change after final p10 read accepted at commit outside no-writer premise','transient midphase change restored before phase proof can escape detection'],recovery_read_bytes_removed_arithmetic=241111289856,resources=dict(cpu='cpuset0; quota 1 CPU',memory_bytes=1073741824,memory_peaks_bytes=peaks,network='none',devices_added=False,capabilities='none',user='501:20',serial=True),scope='host fixtures only; no target build or image')
(R/'evidence/validation.json').write_text(json.dumps(v,indent=2)+'\n')
handoff=dict(status='INDEPENDENT_OFFLINE_REVIEW_COMPLETE',decision='ACCEPT_BOUNDED_SOURCE_UNDER_INSPECTED_FIXED_GRAPH__HOLD_FUTURE_IMAGE_INTEGRATION',report='REPORT.md',validation='evidence/validation.json',original_hashes='evidence/original-sha256.json',originals_unchanged=True,source_regression_found_within_fixed_graph=False,reachable_ordinary_concurrent_p10_writer_found=False,invariant_scope='Inspected pinned stock-only init/proxy/daemon/helper/effective-policy graph; must be reestablished against final future image.',findings=[dict(priority='P2',kind='guarantee_precision',title='Persistent mutation must be observed by a later full proof to be rejected; final-sample race can commit',minimal_fix='Qualify REPORT/HANDOFF wording and retain final-sample witness; rely on real writer exclusion through receipt.'),dict(priority='P3',kind='descriptor_precision',title='Same-node open-file-description replacement and access/CLOEXEC changes are not detected by stat binding',minimal_fix='Narrow replacement claims and document no-rebinding source premise; any optional flag checks require separate source review.'),dict(priority='P1',kind='existing_separate_integration_blocker',title='Frozen two-role helper and fixed prior core binding cannot automatically admit future five-role manifest',minimal_fix='Separate compatible helper/core/manifest design and review; preserve current checks/refusals.')],tests=v['tests'],total_test_methods=v['total_test_methods'],frozen_candidate_sha256='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f',physical_GO=False,flash_GO=False,timing_GO=False,new_image=False,target_build=False,source_or_helper_relaxed=False,subagents=False,network=False,device_access=False,deployment_instructions=False)
(R/'HANDOFF.json').write_text(json.dumps(handoff,indent=2)+'\n')
p=R/'REPORT.md';s=p.read_text();s=s.replace('Validation results and resource receipts are recorded in `evidence/validation.json` after the fixture completes.','All **57 test methods passed**: 23 baseline sessions, 23 revised sessions, one existing direct-guard method, one existing handoff method, eight new boundary methods and one new real-exec/failure method. The symbolic model also passed. The freshly rebuilt vendored libsepol reproduces all 144 effective-policy rows exactly; the separate permissive/capability2/attribute/ioctl assertions pass. The highest container memory peak was **242,610,176 bytes**, below 1GiB. There were no sanitizer failures; compile-time `_GNU_SOURCE` redefinition warnings are retained. Results and resource receipts are recorded in `evidence/validation.json`.')
p.write_text(s)
(R/'README.md').write_text('''# Independent future recovery phase review

Question: Does removing per-WRITE/SKIP p10 hashing preserve the actual pinned phase proofs and exclude ordinary reachable concurrent p10 writers in the exact fixed RAM graph?

Status: complete. ACCEPT bounded source under the inspected fixed-graph premise; HOLD final future-image integration. No physical/flash/timing GO.

Important outputs:

- [REPORT.md](REPORT.md): priority findings, minimal corrections, writer/descriptor/state analysis and narrow decision.
- [HANDOFF.json](HANDOFF.json): machine-readable decision and separate five-role helper integration blocker.
- [evidence/validation.json](evidence/validation.json): 57 passing host test methods, clean policy rebuild/query, resource receipts and counterexamples.
- `snapshot/`: unchanged reviewed source/evidence; `evidence/original-sha256.json` records all 393 initial input hashes.
- `fixture/`: separately copied ordinary-file/socketpair host tests; `scripts/` records review additions and verification. Production C/header bytes remain unchanged.

Continuation: read REPORT.md and HANDOFF.json. Carry the P2 final-sample and P3 same-node descriptor qualifications with the source-only acceptance. Keep the existing two-role helper and all its checks unchanged; five-role helper/core/manifest compatibility is separate blocked integration work. Any final future RAM image must reestablish the exact writer invariant against its final services, executables, effective policy, labels, manifest and bindings. No deployment or device operation is authorized by this review.
''')
# Final artifact inventory is generated after all outputs have settled.
rows=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS':rows.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R)))
(R/'SHA256SUMS').write_text('\n'.join(rows)+'\n')
print(json.dumps(dict(passed=True,methods=v['total_test_methods'],peak=max(peaks.values()),inventory_files=len(rows))))
