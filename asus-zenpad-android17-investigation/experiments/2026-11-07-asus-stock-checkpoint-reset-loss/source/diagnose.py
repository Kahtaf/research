"""Read only named public boot artifact; decode bounded stock functions, never package."""
from pathlib import Path
import sys, json, hashlib, bisect, struct
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent

def boundary(event,args):
 if event=='open':
  s=str(args[0])
  assert not any(x in s for x in ['/private/', '/device-backup/', 'root_shell_wifi.py','mtk-su-mirror-b','/dev/'])
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'): raise RuntimeError(event)
sys.addaudithook(boundary)
sys.path.insert(0,str(WORK/'2026-11-07-asus-stock-kernel-version-control/source'))
import bootformat as b, kallsyms
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
blob=(WORK/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img').read_bytes()
assert b.sha(blob)=='dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427'
_,kernel,_,_=b.parse_image(blob)
raw,dt=b.ungzip(kernel[512:])
assert b.sha(raw)=='db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
symbols,sym,base,addresses=kallsyms.decode(raw)
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)

def owner(a):
 i=bisect.bisect_right(addresses,a)-1
 return symbols[i][1]+'+'+hex(a-addresses[i])

def dump(names,filename):
 out=[];meta=[]
 for name in names:
  a=sym[name] if isinstance(name,str) else name[0]
  end=next(x for x in addresses if x>a) if isinstance(name,str) else name[1]
  n=name if isinstance(name,str) else owner(a)
  data=raw[a-base:end-base]
  meta.append(dict(name=n,address=hex(a),end=hex(end),bytes=len(data),sha256=b.sha(data)))
  out.append('\n'+json.dumps(meta[-1]))
  for i in cs.disasm(data,a):
   extra=''
   if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'): extra=' ; '+owner(int(i.op_str[1:],16))
   out.append(f'{i.address:016x} {i.bytes.hex()} {i.mnemonic} {i.op_str}{extra}')
 (ROOT/'evidence'/filename).write_text('\n'.join(out)+'\n')
 return meta
if __name__=='__main__':
 selected=[(hex(a),n) for a,n in symbols if any(x in n for x in ['wdt','flush','cache','ram_console','sram_log','__cpu_setup','mair','get_wd_api'])]
 (ROOT/'evidence/symbols.json').write_text(json.dumps(selected,indent=2)+'\n')
 names=['ram_console_check_header','ram_console_early_init','ram_console_write','sram_log_save','aee_rr_show_fiq_step','aee_rr_rec_fiq_step','aee_rr_curr_fiq_step','mtk_arch_reset_handle','arch_reset','mtk_wdt_restart','get_wd_api','__cpu_setup']
 print(json.dumps(dump(names,'core.disasm'),indent=2))
 # Complete only the bounded dependent mapping/callback/reader evidence.
 dump(['wd_sw_reset','wdt_arch_reset','wd_api_init','vmap','vmap_page_range_noflush'], 'mapping-reset.disasm')
 dump(['ram_console_show','aee_rr_reboot_reason_proc_open','aee_rr_reboot_reason_show'], 'reader.disasm')
 # Literals are data, so retain their bytes rather than disassembling them.
 spans=[('mapping protection',0xffffffc000f413b8,24),('MAIR load/program',0xffffffc000ad09f8,8),
        ('MAIR literal',0xffffffc000ad0a30,8),('watchdog callback',0xffffffc00106bca0,8),
        ('reset barrier and trigger',0xffffffc000800b8c,20),('proc show pointer',0xffffffc0006aee68,8),
        ('saved fiq callback',0xffffffc001002ca8,8),('copy before clear',0xffffffc000f414e4,20),
        ('clear call',0xffffffc000f41564,4)]
 data=[]
 for label,a,n in spans:
  value=raw[a-base:a-base+n]
  data.append(dict(label=label,address=hex(a),raw_offset=hex(a-base),bytes=n,hex=value.hex(),sha256=b.sha(value)))
 # Recheck public candidate identity and that relevant reset/mapping/reader bodies
 # were not silently altered, apart from its documented wrapper and notifier BL.
 candidate=(WORK/'2026-11-07-asus-stock-checkpoint-readback-control/artifacts/candidate.img').read_bytes()
 assert b.sha(candidate)=='042c1a63a699f6a978c589341801580a5c4f46fde23832ad174f42c763940260'
 _,ck,_,_=b.parse_image(candidate)
 cr,_=b.ungzip(ck[512:])
 assert b.sha(cr)=='610c7e459f8493ab668f59834c9db469e7a98b2e658a610d51ca6233c4cdcf91'
 verified=[]
 for name in ['ram_console_early_init','ram_console_check_header','aee_rr_rec_fiq_step','aee_rr_curr_fiq_step','arch_reset','wd_sw_reset','wdt_arch_reset','__cpu_setup','vmap','vmap_page_range_noflush','ram_console_show','aee_rr_reboot_reason_show']:
  a=sym[name]; e=next(x for x in addresses if x>a)
  assert raw[a-base:e-base]==cr[a-base:e-base]
  verified.append(name)
 # Copy only the parent's selected public result fields, never raw console/private payload.
 p=WORK/'2026-11-07-asus-stock-checkpoint-readback-trial/evidence/RESULT.json'
 result=json.loads(p.read_text())
 keep=['outcome','boot_id','candidate_p10_sha256','saved_fiq','before_reset_values','complete_console_read','console_sha256','missing_marker_does_not_prove_linux49_nonexecution']
 selected={k:result[k] for k in keep}
 (ROOT/'evidence/physical-selected.json').write_text(json.dumps(selected,indent=2)+'\n')
 evidence=dict(donor_sha256=b.sha(blob),stock_raw_Image_sha256=b.sha(raw),candidate_sha256=b.sha(candidate),candidate_raw_Image_sha256=b.sha(cr),base=hex(base),mapping_protection='0x02e0000000000703',attr_index=0,mair_el1=hex(struct.unpack_from('<Q',raw,0xffffffc000ad0a30-base)[0]),mair_attr0='0x00 (Device-nGnRnE)',retained_physical_range=['0x44400000','0x44480000'],unchanged_candidate_functions=verified,spans=data)
 (ROOT/'evidence/exact.json').write_text(json.dumps(evidence,indent=2)+'\n')
 # Keep the symbol index bounded to functions actually emitted.
 names={x['name'] for fn in ['core.disasm','mapping-reset.disasm','reader.disasm'] for line in (ROOT/'evidence'/fn).read_text().splitlines() if line.startswith('{') for x in [json.loads(line)]}
 (ROOT/'evidence/symbols.json').write_text(json.dumps([(hex(sym[n]),n) for n in sorted(names) if n in sym],indent=2)+'\n')
