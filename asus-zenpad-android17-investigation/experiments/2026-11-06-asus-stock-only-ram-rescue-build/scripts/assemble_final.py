from pathlib import Path
import sys,hashlib,json
R=Path(__file__).resolve().parents[1];A=R/'artifacts';sys.path.insert(0,str(R/'source'));import bootformat as b
sha=lambda x:hashlib.sha256(x).hexdigest()
helper=(A/'p10-restore').read_bytes();b.elf_static(helper)
capsule=b.make_cpio({'sbin/p10-restore':(0o100700,0,0,helper)})
gz=(A/'core.cpio.gz').read_bytes();combined=gz+capsule
assert len(combined)<=0x400000
h=(A/'base-header').read_bytes();k=(A/'base-kernel').read_bytes();w=(A/'base-wrapper').read_bytes()
image=b.make_image(h,k,b.wrap(w,combined));full=image+bytes(b.PARTITION_SIZE-len(image))
out=A/'candidate';out.mkdir(exist_ok=False)
(out/'UNAPPROVED-STOCK-ONLY.img').write_bytes(image);(out/'UNAPPROVED-STOCK-ONLY.p10.raw').write_bytes(full)
(out/'helper.cpio').write_bytes(capsule)
contract=dict(format='P10R1',mode='STOCK-ONLY/UNAPPROVED',armed=False,execute_approved=False,manifest_records=2, timing_qualified=False, physical_GO=False, capability_scope=['original_SYSTEM','original_BOOT','terminal_fixed_original_p10_only'], manifest_sha256=sha((A/'original-stock.manifest').read_bytes()),
 image_sha256=sha(image),p10_full_sha256=sha(full),image_bytes=len(image),p10_bytes=len(full),
 payload_sha256=b.RECOVERY_SHA,helper_sha256=sha(helper),core_gzip_sha256=sha(gz),
 policy_sha256=sha((A/'restore-sepolicy').read_bytes()),contexts_sha256=sha((A/'file_contexts.bin').read_bytes()),
 kernel_sha256=sha(k),ramdisk_bytes=len(combined),reservation_headroom=0x400000-len(combined),
 physical_validation=False,trust_boundary='Fixed core plus RAM helper identity; parent externally pins full final image. No runtime source/hash/partition overrides.',
 activation_gate='Two original target roles; not deployment approved. Public host ARMED=False and TIMING_QUALIFIED=False. Parent independent review and physical timing/commissioning remain required. Future five-role profiles refused.')
(out/'session-contract.UNAPPROVED.json').write_text(json.dumps(contract,indent=2)+'\n')
(R/'source/generated_host_binding.py').write_text('PRIOR_SHA = '+repr(sha(full))+'\nHELPER_SHA = '+repr(sha(helper))+'\nARMED = False\n')
print(json.dumps(contract,indent=2))
