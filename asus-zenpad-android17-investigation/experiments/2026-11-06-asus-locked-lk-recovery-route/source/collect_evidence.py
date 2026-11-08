"""Pin only public firmware and named receipts; never open private/ or full SYSTEM."""
from pathlib import Path
import hashlib,json,struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
S=Path(__file__).resolve().parents[1];W=S.parent
paths=[
'AGENTS.md',
'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin',
'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin',
'2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin',
'2026-11-05-asus-boot-access-audit/evidence/live-lk-official-comparison.json',
'2026-11-06-asus-lk-linux49-handoff/REPORT.md',
'2026-11-06-asus-lk-linux49-handoff/evidence/input-receipts.json',
'2026-11-06-asus-stock-userdata-recovery/REPORT.md',
'2026-11-06-asus-stock-userdata-recovery/HANDOFF.json',
'2026-11-06-asus-stock-userdata-recovery/evidence/parent-contract-acceptance.json',
'2026-11-06-asus-stock-userdata-recovery/evidence/partition-map.json',
'2026-11-06-asus-factory-state-preservation/evidence/parent-preservation-acceptance.json',
'2026-11-05-asus-boot-access-audit/evidence/fastboot-secure.jsonl',
'2026-11-05-asus-boot-access-audit/evidence/fastboot-unlocked.jsonl',
'2026-11-05-asus-boot-access-audit/evidence/fastboot-product.jsonl',
'2026-11-05-asus-boot-access-audit/scripts/backup_partition_usb.py',
'2026-11-05-asus-mt8163-kernel-bringup/sources/kernel/include/linux/mmc/mmc.h',
'2026-11-05-asus-mt8163-kernel-bringup/sources/kernel/include/linux/mmc/core.h',
]
pins=[]
for name in paths:
 p=W/name;assert p.stat().st_size<20*1024*1024;data=p.read_bytes();h=hashlib.sha256(data).hexdigest()
 if name.endswith('/recovery.bin'):assert len(data)==16740352 and h=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
 pins.append(dict(path=name,bytes=len(data),sha256=h))
(S/'evidence/input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
B=(W/paths[1]).read_bytes();base=0x41e00000
ipins=json.loads((S/'evidence/instruction-pins.json').read_text());md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
lines=[]
for addr,h in sorted(ipins.items()):
 a=int(addr,16);raw=bytes.fromhex(h);assert B[a-base+512:a-base+512+len(raw)]==raw
 decoded=list(md.disasm(raw,a));assert len(decoded)==1
 i=decoded[0];lines.append(f'{a:08x} {h:10} {i.mnemonic:10} {i.op_str}')
(S/'evidence/executed-disassembly.txt').write_text('# Exact original instructions executed by fixtures; sorted union, not a single trace. External stubs excluded.\n'+'\n'.join(lines)+'\n')
queries={}
for name in ['secure','unlocked','product']:
 p=W/f'2026-11-05-asus-boot-access-audit/evidence/fastboot-{name}.jsonl'
 rows=[json.loads(l) for l in p.read_text().splitlines()]
 queries[name]=[dict(utc=r['utc'],prefix=r['prefix'],payload=r['payload']) for r in rows if r['phase']=='response']
(S/'evidence/saved-identity.json').write_text(json.dumps(queries,indent=2)+'\n')
source=[]
for n in paths[-2:]:
 for line,l in enumerate((W/n).read_text().splitlines(),1):
  if any(k in l for k in ['#define MMC_ERASE_GROUP_START','#define MMC_ERASE_GROUP_END','#define MMC_ERASE\t','#define MMC_TRIM_ARG','#define MMC_ERASE_ARG']):source.append(f'{n}:{line}: {l}')
(S/'evidence/mmc-command-reference.txt').write_text('\n'.join(source)+'\n')
em=json.loads((S/'evidence/emulation.json').read_text())
(S/'evidence/registration.json').write_text(json.dumps(next(c['commands'] for c in em['cases'] if c['name']=='registration'),indent=2)+'\n')
(S/'evidence/checks.json').write_text(json.dumps(dict(inputs_pinned=len(pins),instruction_pins_verified=len(ipins),original_instruction_cases=em['case_count'],original_recovery_copies_match=True,device_operations=False,private_access=False,full_system_read=False),indent=2)+'\n')
print(f'{len(pins)} inputs, {len(ipins)} original instruction pins verified')
