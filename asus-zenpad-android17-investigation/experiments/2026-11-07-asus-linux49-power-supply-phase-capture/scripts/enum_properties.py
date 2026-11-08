from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
h=(R/'source/base/include/linux/power_supply.h').read_bytes();c=(R/'artifacts/resolved.config').read_bytes();s=h.decode();s=s[s.index('enum power_supply_property {'):];s=s[:s.index('};')]
condition='#if (defined CONFIG_USB_AMAZON_DOCK) || (defined CONFIG_POGO_PIN_DOCK)\n\tPOWER_SUPPLY_PROP_DOCK_PRESENT,\n#endif'
assert s.count(condition)==1
active=any((n+'=y').encode() in c or (n+'=m').encode() in c for n in ['CONFIG_USB_AMAZON_DOCK','CONFIG_POGO_PIN_DOCK'])
s=s.replace(condition,'\tPOWER_SUPPLY_PROP_DOCK_PRESENT,' if active else '')
assert '#' not in s
s=re.sub(r'/\*.*?\*/','',s,flags=re.S).split('{',1)[1]
props={};value=-1
for item in s.split(','):
 item=item.strip()
 if not item:continue
 m=re.fullmatch(r'(POWER_SUPPLY_PROP_\w+)(?:\s*=\s*(\d+))?',item);assert m,item
 value=int(m[2]) if m[2] else value+1;props[value]=m[1]
r=dict(source='source/base/include/linux/power_supply.h',source_sha256=hashlib.sha256(h).hexdigest(),config_sha256=hashlib.sha256(c).hexdigest(),dock_present_compiled=active,properties=props)
(R/'evidence/property-enum.json').write_text(json.dumps(r,indent=2)+'\n');print('Exact source/config enum: '+str(len(props))+' values; DOCK_PRESENT='+str(active))
