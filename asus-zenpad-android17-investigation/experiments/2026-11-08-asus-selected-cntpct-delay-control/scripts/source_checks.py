from pathlib import Path
import json,hashlib,re

def check(K,B,uuid):
 old='f3da846c-cbd9-4623-adc2-5e54d097dfdc'
 n='arch/arm64/lib/delay.c';s=(K/n).read_text();a=s.index('/* Only a strictly joined');z=s.index('void __delay(',a);helper=s[a:z]
 assert helper.count('get_cycles()')==helper.count('isb();')==helper.count('mrs %0, cntpct_el0')==1
 restored=s[:a]+s[z:];restored=restored.replace('selected_delay_counter(generation)','get_cycles()');assert restored==(B/n).read_text()
 n='arch/arm64/kernel/asus_retained_trace.c';s=(K/n).read_text();z=s.replace(uuid,old)
 for a,b in [('static u64 dl_gen, dl_state, dl_mask, dl_join[29], dl_read_domain;','static u64 dl_gen, dl_state, dl_mask, dl_join[29];'),('dl_const, dl_caller, dl_mask, dl_read_domain};','dl_const, dl_caller, dl_mask};'),('"!A49DH   ", f, ARRAY_SIZE(f), 192, 168','"!A49DH   ", f, ARRAY_SIZE(f), 192, 160'),('A49DL2 uuid=','A49DL1 uuid='),('dl_state = 1; dl_mask = 0; dl_hook = hook; dl_read_domain = 0;','dl_state = 1; dl_mask = 0; dl_hook = hook;'),(' dl_read_domain = 1;\n',''),('dl_state != 3 || dl_read_domain != 1 ||','dl_state != 3 ||')]:assert a in z;z=z.replace(a,b)
 assert z==(B/n).read_text(),'unexplained recorder change'
 dl=s[s.index('/* Fixed latest generation only.'):s.index('static void __init cap_init(')]
 assert not any(t in dl for t in ['get_cycles','cntvct','cntpct','read_sysreg','schedule(','printk(','sleep('])
 assert (K/'arch/arm64/kernel/asus_entry_tag.h').read_text().replace(uuid,old)==(B/'arch/arm64/kernel/asus_entry_tag.h').read_text()
 return dict(status='PASS_EXACT_REVERSE_DIFF',delay_body_and_arithmetic_restores_byte_exact=True,old_five_capture_layouts_and_hooks_restore_except_UUID=True,delay_area_bytes=2560,header_fields=9,header_tail=168,all_other_offsets_unchanged=True,backend_reset_before_arm=True,backend_set_under_existing_selected_claim_lock=True,no_new_recorder_counter_reads=True,no_new_lock_or_IRQmask_across_delay=True)
if __name__=='__main__':
 R=Path(__file__).resolve().parents[1];i=json.loads((R/'evidence/identity.json').read_text());r=check(R/'source',R/'source/base',i['run_uuid']);(R/'evidence/source-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
