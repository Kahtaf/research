"""Offline check of actual installed candidate DT, unchanged config and ELF receipt."""
from pathlib import Path
import sys,hashlib,json
sys.dont_write_bytecode = True
R=Path(__file__).resolve().parents[1];W=R.parent;P=W/'2026-11-07-asus-early-retained-kernel-probe'
sys.path.insert(0,str(P/'source'))
import bootformat as b
from fdt import parse
image=(P/'artifacts/candidate.img').read_bytes()
assert b.sha(image)=='2a0d400811292ece957bb00f632f56aef8e5967643bd5a0184c10eaeea051533'
h,k,rd,extra=b.parse_image(image);assert not extra
raw,dt=b.ungzip(k[512:]);nodes=parse(dt)[1]
node=nodes['/soc/toprgu@10007000']
assert node['compatible']==b'mediatek,mt8163-rgu\x00mediatek,mt6589-wdt\x00'
assert node['reg']==bytes.fromhex('00000000100070000000000000001000')
assert node.get('status',b'okay\0') in [b'okay\0',b'ok\0']
assert 'clocks' not in node
compiled=(R/'evidence/vm/asus-p00a.dtb').read_bytes()
assert parse(compiled)[1]['/soc/toprgu@10007000']==node
assert nodes['/chosen']['bootargs']==b'androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1\0'
identity=json.loads((R/'evidence/vm/identity.json').read_text())
assert identity['config_sha256']==b.sha((P/'artifacts/resolved.config').read_bytes())=='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696'
source=(R/'evidence/vm/drivers__watchdog__mtk_wdt.c').read_text()
assert b.sha(source.encode())==identity['source_pins']['drivers/watchdog/mtk_wdt.c']
assert '#if defined(CONFIG_DOUGLAS) || defined(CONFIG_GIZA)' in source
assert '\tmtk_wdt_stop(&mtk_wdt->wdt_dev);' in source
assembly=(R/'evidence/vm/disassembly-mtk_wdt_probe.txt').read_text()
assert 'ffffff80088093a8:' in assembly and '<mtk_wdt_stop>' in assembly
stock=json.loads((W/'2026-11-06-asus-android17-orchestration/evidence/stock-watchdog-root-facts.json').read_text())
result=dict(status='PASS',actual_candidate_sha256=b.sha(image),packaged_dt_sha256=b.sha(dt),compiled_dt_sha256=b.sha(compiled),exact_candidate_wdt_node_matches_compiled=True,compatible=node['compatible'].rstrip(b'\0').decode().split('\0'),reg='0x10007000 + 0x1000',dt_status='okay (absent property)',clocks_property=False,config_sha256=identity['config_sha256'],elf_probe_calls_stop='ffffff80088093a8 -> ffffff8008808cf4',kicker_symbols_absent=identity['absent_symbols'],stock_facts_boot_id=stock['boot_id'],device_contacted=False,builds=0,new_candidate=False)
(R/'evidence/offline-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
