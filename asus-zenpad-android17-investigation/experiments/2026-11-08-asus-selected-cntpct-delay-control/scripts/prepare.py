from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[1];B=R/'source/base';i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid'];old='f3da846c-cbd9-4623-adc2-5e54d097dfdc'
a=json.loads((R/'evidence/actual-base.json').read_text());assert a['config_sha256']==i['config_sha256'] and a['image_sha256']==i['base_compiled_sha256']
files={};n='arch/arm64/lib/delay.c';s=(B/n).read_text()
helper='''/* Only a strictly joined nonzero delay cookie selects this raw read route. */
static __always_inline cycles_t selected_delay_counter(u64 generation)
{
	cycles_t counter;

	if (!generation)
		return get_cycles();
	isb();
	asm volatile("mrs %0, cntpct_el0" : "=r" (counter));
	return counter;
}

'''
s=s.replace('void __delay(',helper+'void __delay(',1).replace('start = get_cycles();','start = selected_delay_counter(generation);',1).replace('counter = get_cycles();','counter = selected_delay_counter(generation);',1);files[n]=s
n='arch/arm64/kernel/asus_entry_tag.h';files[n]=(B/n).read_text().replace(old,u)
n='arch/arm64/kernel/asus_retained_trace.c';s=(B/n).read_text().replace(old,u)
s=s.replace('static u64 dl_gen, dl_state, dl_mask, dl_join[29];','static u64 dl_gen, dl_state, dl_mask, dl_join[29], dl_read_domain;')
s=s.replace('dl_const, dl_caller, dl_mask};','dl_const, dl_caller, dl_mask, dl_read_domain};').replace('"!A49DH   ", f, ARRAY_SIZE(f), 192, 160','"!A49DH   ", f, ARRAY_SIZE(f), 192, 168')
s=s.replace('A49DL1 uuid=','A49DL2 uuid=').replace('dl_state = 1; dl_mask = 0; dl_hook = hook;','dl_state = 1; dl_mask = 0; dl_hook = hook; dl_read_domain = 0;').replace('dl_state = 3;\n gen = dl_gen;','dl_state = 3;\n dl_read_domain = 1;\n gen = dl_gen;')
s=s.replace('stage >= 7 || gen != dl_gen || dl_state != 3 ||','stage >= 7 || gen != dl_gen || dl_state != 3 || dl_read_domain != 1 ||')
files[n]=s
pins={};diff=[]
for n,s in files.items():
 b=(B/n).read_bytes();p=R/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 pins[n]=dict(before=hashlib.sha256(b).hexdigest(),after=hashlib.sha256(s.encode()).hexdigest());diff.extend(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(R/'evidence/preserved-source-pins.json').write_text(json.dumps({n:v for n,v in a['source_pins'].items() if n not in pins and not n.startswith('out-provenance/')},indent=2)+'\n')
print('Prepared three kernel files; old delay body restores by two call substitutions')
