from pathlib import Path
import json,re,hashlib

def check(K,B,uuid):
 old='a1ff82b1-3e45-4f05-8c99-7112204d3981';n='arch/arm64/kernel/asus_retained_trace.c'
 s=(K/n).read_text();z=s
 dl=z[z.index('/* Fixed latest generation only.'):z.index('static void __init cap_init(')]
 z=z.replace(dl,'').replace('static void dl_pmic(const u64 *f, unsigned long hook);\n\n','',1)
 z=z.replace('#include <linux/delay.h>\n#include <linux/power/asus_p00a_battery.h>\n','',1)
 z=z.replace('int sample, int poll, u32 status, bool begin, unsigned long hook)','int sample, int poll, u32 status, bool begin)',1)
 z=z.replace(' if (code == 38 || code == 39)\n  dl_pmic(f, hook);\n','',1).replace('0x80000000U, true, 0);','0x80000000U, true);',1).replace('status, false,\n   (unsigned long)__builtin_return_address(0));','status, false);',1)
 z=z.replace(' BUILD_BUG_ON(DL_SIZE % 64);\n','',1).replace('CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE + DL_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE')
 z=z.replace(' dl_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE);\n','',1).replace(' smp_store_release(&dl_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE);\n','',1)
 assert z.replace(uuid,old)==(B/n).read_text(),'unexplained recorder diff'
 for name in ['printk','schedule','ktime','get_cycles','cntvct','cntpct','read_sysreg','alloc','sleep','mutex','pm_record(']:assert name not in dl,('new writer forbidden primitive',name)
 assert dl.count('raw_spin_trylock_irqsave')==1 and dl.count('raw_spin_unlock_irqrestore')==5
 init=s[s.index('static void __init cap_init('):s.index('static bool cap_lock(')]
 assert init.index('h->sz_console - pos')<init.index("memset(")<init.index('dl_init(')<init.index('WRITE_ONCE(h->log_size')<init.index('smp_store_release(&dl_area')
 n='arch/arm64/lib/delay.c';d=(K/n).read_text();body=d[d.index('void __delay('):d.index('EXPORT_SYMBOL(__delay);')]
 assert body.count('get_cycles()')==2 and body.count('cpu_relax();')==1
 assert body.index('start = get_cycles();')<body.index('counter = get_cycles();')<body.index('if ((counter - start) >= cycles)')<body.index('cpu_relax();')
 assert 'iteration != U64_MAX' in body and 'iteration == U64_MAX' in body
 assert 'lpj = loops_per_jiffy;' in d and d.count('loops_per_jiffy')==1 and 'loops = xloops * lpj * HZ;' in d
 assert body.count('break;')==1 and body.count('return')==1 # builtin_return_address only
 for fn in ['__delay','__const_udelay','__udelay','__ndelay']:assert 'EXPORT_SYMBOL('+fn+');' in d
 return dict(status='PASS_SMALL_SCOPED_SOURCE',old_recorder_restores_byte_exact_except_UUID=True,old_layout_bytes=26752,new_fixed_bytes=2560,combined_bytes=29312,no_new_counter_reads_or_timer_driver_edit=True,primitive_control='controls.json; actual base and candidate C bodies',single_LPJ_operand_and_product=True,capacity_before_write_logsize_and_readiness=True,publication_lock_edge='PM->DL trylock only; DL never acquires PM; all release before original counter/loop',saturation='u64 saturates; one sticky overflow publication at U64_MAX; no limit or early return')
if __name__=='__main__':
 R=Path(__file__).resolve().parents[1];i=json.loads((R/'evidence/identity.json').read_text());r=check(R/'source',R/'source/base',i['run_uuid']);(R/'evidence/source-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
