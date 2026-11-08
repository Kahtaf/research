"""Bounded static receipts for the already built single candidate; no replays/builds."""
from pathlib import Path
import json,sys,struct,re,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
sys.path.insert(0,str(W/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b,kallsyms
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
p=json.loads((R/'evidence/packaging-receipt.json').read_text())
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
_,k,_,_=b.parse_image((W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes());raw,dt=b.ungzip(k[512:]);ss,s,base,aa=kallsyms.decode(raw);cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
def span(name):
 a=s[name];end=next(x for x in aa if x>a);return a,raw[a-base:end-base]
def listing(a,v):return ''.join(f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n' for i in cs.disasm(v,a))
console=0xffffffc001002c28;obj=raw[console-base:console-base+88];flags=struct.unpack_from('<H',obj,64)[0]
assert obj[:16].split(b'\0')[0]==b'ram' and struct.unpack_from('<Q',obj,16)[0]==s['ram_console_write'] and flags&1
names=['register_console','printk','vprintk_emit','ram_console_write','sram_log_save','aee_rr_reboot_reason_proc_open','aee_rr_reboot_reason_show','ram_console_early_init','__memset_io']
func=[]
for name in names:
 a,v=span(name);func.append(dict(name=name,address=hex(a),bytes=len(v),sha256=b.sha(v)));(R/'evidence'/('stock-'+name+'.disasm')).write_text(listing(a,v))
register_a,register=span('register_console');ins=list(cs.disasm(register,register_a))
checks=[(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str) for i in ins if '#0x40]' in i.op_str or (i.mnemonic in ('tbz','tbnz') and ', #0,' in i.op_str)]
assert any('#0x40]' in i.op_str and i.mnemonic=='ldrh' for i in ins)
helper_source=(W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/source/init.c').read_text()
assert not re.findall(r'"/proc/[^"\n]*',helper_source) and not re.search(r'\b(?:execve|execl|system|popen|fork|vfork)\s*\(',helper_source)
assert 'alarm(60)' in helper_source and 'reboot(RB_AUTOBOOT)' in helper_source
# Preserve bounded source context only as interpretation aid; shipped instructions are authoritative.
source_root=W/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
excerpts=[]
for rel,ranges in [('drivers/misc/mediatek/ram_console/mtk_ram_console.c',[(443,464),(2199,2210),(2372,2475)]),('drivers/misc/mediatek/aee/common/reboot-reason.c',[(45,72)]),('kernel/printk/printk.c',[(2798,2828)]),('arch/arm64/kernel/head.S',[(435,469)])]:
 content=(source_root/rel).read_text().splitlines();excerpts.append('\n'+rel+'\n');excerpts.extend(f'{n}: {content[n-1]}' for lo,hi in ranges for n in range(lo,min(hi,len(content))+1))
(R/'evidence/source-context.txt').write_text('\n'.join(excerpts)+'\n')
lk=W/'2026-11-06-asus-full-boot-lk-contract/evidence/reachable-disassembly.txt';text=lk.read_text();lines=text.splitlines();ranges=[(i,min(i+12,len(lines))) for i,l in enumerate(lines) if l.startswith(('41e1cfd4 ','41e1e4a8 '))]
(R/'evidence/LK-decompression-bounds.disasm').write_text('\n'.join(x for lo,hi in ranges for x in lines[lo:hi])+'\n')
# Copy prior exact mapping/reset proofs (public only); candidate changes only enumerated raw spans.
for fn in ['mapping-reset.disasm','exact.json']:(R/'evidence'/('prior-'+fn)).write_bytes((W/'2026-11-07-asus-stock-checkpoint-reset-loss/evidence'/fn).read_bytes())
result=dict(status='ONE_CANDIDATE_AND_ONE_ISOLATED_PLAN_COMPLETE_NO_PHYSICAL_GO',candidate=p['candidate'],full_p10=p['full_p10'],console_object=dict(address=hex(console),bytes=obj.hex(),flags=hex(flags),CON_PRINTBUFFER=True,write=hex(s['ram_console_write'])),register_console_flags_instructions=checks,original_functions=func,slot_callgraph=dict(slot='aee_rr_show_idvfs_ctrl_reg',bounds=['0xffffffc000696b14','0xffffffc000696c74'],only_live_pointer='0xffffffc001002ef8 inside diagnostic callback table traversed by aee_rr_reboot_reason_show',other_pointer='0xffffffc000c0a948 is decoded kallsyms address-table entry, not a live callback',direct_external_branches=0,scope='Source matches sole diagnostic callback use; shipped callback-loop/proc-open bodies and pointers retained in evidence. No export/interface added. Recovery helper never opens this proc path. Next normal BOOT diagnostic reader is unmodified.',helper_source_sha256=b.sha(helper_source.encode()),helper_no_proc_subpaths_no_process_launch=True),loader=dict(pinned_LK_sha256='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765',decompression_capacity='0x1c00000',load_base='0x40080000',actual_raw_output_bytes=p['raw_after']['bytes'],end=hex(0x40080000+p['raw_after']['bytes']),original_reserved_kernel_end='0x41335000',entry_BSS_clear_after_return=True,late_wrapper_in_original_mapped_text=True,model='Pinned exact LK disassembly + host raw-inflate semantic model; not LK execution or entry-state proof'),readback='Saved buffer is the exact incoming 0x80000-byte snapshot before stock current clear. NULL skips; off_console in [0x400,0x80000), size nonzero <= 0x80000-off, start=0; precision=min(size,234); actual saved+off passed as %.*s. Original clear always runs. register_console CON_PRINTBUFFER replays printk ring into cleared current region; physical retention remains untested.',plan=json.loads((R/'evidence/plan-isolation-receipt.json').read_text()),experiment2_result=json.loads((W/'2026-11-07-asus-linux49-entry-text-r2-trial/evidence/RESULT.json').read_text())['outcome'])
(R/'evidence/completion.json').write_text(json.dumps(result,indent=2)+'\n')
# Exact tool and input receipts: no subprocesses; list only files created within this spike.
manifest={str(f.relative_to(R)):dict(bytes=f.stat().st_size,sha256=b.sha(f.read_bytes())) for folder in ['source','qa','artifacts','evidence'] for f in (R/folder).iterdir() if f.is_file() and f.name!='file-manifest.json'}
(R/'evidence/file-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','candidate','full_p10','console_object','register_console_flags_instructions')},indent=2))
