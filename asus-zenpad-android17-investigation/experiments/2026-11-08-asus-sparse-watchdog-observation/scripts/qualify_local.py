"""Bind public register semantics and parser names to this actual source/ELF/map."""
from pathlib import Path
import hashlib,json,re,sys
R=Path(__file__).resolve().parents[1];S=R/'source';E=R/'evidence'
sys.path.insert(0,str(S));import bootformat as b,fdt
blob=(R/'artifacts/Image.gz-dtb').read_bytes();raw,dt=b.ungzip(blob)
_,nodes,_=fdt.parse(dt);_,rn,_=fdt.parse((R/'artifacts/runtime.dtb').read_bytes())
wd=[(p,v) for p,v in nodes.items() if b'mediatek,mt6589-wdt' in v.get('compatible',b'')];assert len(wd)==1
p,v=wd[0];assert rn[p]==v and v['reg']==bytes.fromhex('00000000100070000000000000001000')
assert 'status' not in v or v['status'] in [b'okay\0',b'ok\0']
# Byte-identical full compiled/runtime DT is the preservation proof; list all asus properties for review.
asus_props={p:[n for n in v if n.startswith('asus,')] for p,v in nodes.items() if any(n.startswith('asus,') for n in v)}
source=(S/'drivers/watchdog/mtk_wdt.c').read_text();base=(S/'base/drivers/watchdog/mtk_wdt.c').read_text()
def fn(text,name):
 a=text.index('static int '+name+'(');return text[a:text.index('\n}',a)+2]
stop=fn(source,'mtk_wdt_stop');probe=fn(source,'mtk_wdt_probe');restart=fn(source,'mtk_reset_handler')
assert stop.count('readl(wdt_base + WDT_MODE)')==2 and stop.count('iowrite32(reg, wdt_base + WDT_MODE)')==1
assert restart.count('__raw_readl(wdt_base + WDT_STATUS)')==1 and fn(base,'mtk_reset_handler').count('__raw_readl(wdt_base + WDT_STATUS)')==1
assert probe.count('ioread32(mtk_wdt->wdt_base + WDT_REQ_MODE)')==2
assert probe.count('ioread32(mtk_wdt->wdt_base + WDT_REQ_IRQ_EN)')==2
assert '__raw_readl(mtk_wdt->wdt_base + WDT_REQ_MODE)' in probe
assert probe.index('rtc_mark_quiescent(0)')<probe.index('req_mode = ioread32')<probe.index('req_irq_en = ioread32')<probe.index('ASUS_WDT_PROBE_DONE')
assert source.count('arch_initcall(mtk_wdt_driver_init)')==1
report=dict(status='PASS_SOURCE_QUALIFIED_READS_AND_ACTUAL_MAP',driver_sha256=hashlib.sha256(source.encode()).hexdigest(),base_driver_sha256=hashlib.sha256(base.encode()).hexdigest(),node=p,MMIO_resource='0x10007000 + 0x1000 bytes; unchanged devm_ioremap_resource mapping',compatible=v['compatible'].rstrip(b'\0').decode().split('\0'),IRQ='Both IRQ parse/request and FIQ request/failure blocks are #if 0; no linked IRQ failure branch, no invented IRQ marker',registration='arch_initcall 3; watchdog_register_device can defer before watchdog subsys_initcall 4s. probe_done rc=0 is the original probe return, not proof later deferred registration succeeds',registers={
 'MODE':dict(offset='0x00',enable_bit=0,key='0x22000000',original='readl; clear EN; OR key; iowrite32 once',added='reuse original read before-value; exactly one readl after original keyed write; record after read; no lock spans MMIO',read_qualification='existing driver uses ordinary MODE reads in stop/start/proc. Its explicit STATUS-clear comment concerns writes to MODE. No extra status read or MODE write.'),
 'REQ_MODE':dict(offset='0x30',key='0x33000000',original='one __raw_readl/write and one ioread32/iowrite32 RMW per probe; enable request bits18/0, clear debug bit19',added='one ioread32 at end after original configuration and rtc_mark_quiescent(0)'),
 'REQ_IRQ_EN':dict(offset='0x34',key='0x44000000',original='ioread32/iowrite32 RMW; clear request IRQ bits18/0',added='one ioread32 at end after original configuration and rtc_mark_quiescent(0)')},
read_semantics_limit='Qualified against this exact driver\'s repeated configuration RMW semantics. No destructive/read-clear semantics are indicated for these configuration registers in this source; no claim of independently measured silicon behavior. No WDT_STATUS/timeout/counter/status dump was added.',restart='marker with LR before original single STATUS0x0c-to-NONRST0x20 backup; original MODE and SWRST0x14/key0x1209 operations and delays preserved',default31='software default only; this probe stops and does not call start or set_timeout; legacy kicker gate CONFIG_MTK_WATCHDOG is disabled',asus_DT_properties=asus_props,charging_permission='unchanged absent as compiled/runtime DT are byte-identical to exact sparse base',runtime=False)
(E/'register-qualification.json').write_text(json.dumps(report,indent=2)+'\n')
# Small map-bound parser controls use synthetic callers derived from actual call instructions.
sys.path.insert(0,str(R/'scripts'));import decode_sparse as d
rows=d.load_map(R/'artifacts/System.map.gz');dis=(E/'scoped-linked.disasm').read_text()
def linked_fn(name):
 a=dis.index('<'+name+'>:');z=dis.find('\n/srv/',a);return dis[a:z if z>=0 else None]
probe_dis=linked_fn('mtk_wdt_probe');m=re.search(r'^([0-9a-f]+):[^\n]*\bbl\s+[0-9a-f]+ <mtk_wdt_stop>',probe_dis,re.M);assert m
lr=int(m[1],16)+4
entry=json.loads((S/'arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines()[0].split(' ',2)[2]).rstrip('\n')
i=json.loads((E/'identity.json').read_text());text=entry+'\n'+i['mode']+'\n'+i['watchdog_prefix']+f'event=stop before=00000000 after=00000000 en_before=0 en_after=0 caller={lr:016x}\n'
result=d.decode(text,rows);assert result['liveness']['status']=='UNKNOWN_STOP' and result['watchdog']['stop'][0]['actual_probe_route']
notifier=linked_fn('notifier_call_chain');m=re.search(r'^([0-9a-f]+):[^\n]*\bblr\s+x\d+',notifier,re.M);assert m
lr=int(m[1],16)+4
text=entry+'\n'+i['mode']+'\n'+i['watchdog_prefix']+f'event=restart route=mtk_reset_handler caller={lr:016x}\n'
x=d.decode(text,rows)['watchdog'];assert x['restart'][0]['caller_route']=='notifier_call_chain'
(E/'map-parser-controls.json').write_text(json.dumps(dict(status='PASS_GENUINE_MAP_NAMES',synthetic=True,stop_caller=result['watchdog']['stop'][0],restart_caller=x['restart'][0],pre_PID1_liveness=result['liveness']['status'],raw_callers_published=False),indent=2)+'\n')
print('PASS source-qualified registers, unchanged resource/DT, genuine-map stop and notifier caller names')
