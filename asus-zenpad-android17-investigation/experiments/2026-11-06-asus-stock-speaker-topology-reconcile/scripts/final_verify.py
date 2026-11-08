import hashlib,json,re,struct,resource
from pathlib import Path
from bounded import ROOT,run
from binary_evidence import fdt
H=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
for x in json.loads((ROOT/'evidence/input-pins.json').read_text()):
 assert H((ROOT.parent/x['path']).read_bytes())==x['sha256'],x['path']
 assert H((ROOT/x['copy']).read_bytes())==x['sha256'],x['copy']
checks.append('All consulted copied public source/config/firmware/observation inputs still match original paths and hashes')
for label in ['stock-public','bmc']:
 raw=(ROOT/'inputs'/label/'Image').read_bytes();obj=(ROOT/f'evidence/{label}-actual-bytes.elf').read_bytes()
 assert obj[64:64+len(raw)]==raw
 meta=json.loads((ROOT/f'evidence/{label}-kallsyms.json').read_text());assert H(raw)==meta['Image_sha256']
 text=(ROOT/f'evidence/{label}-disassembly.txt').read_text()
 assert re.search(r'\bbl\s+0x[0-9a-f]+ <Speaker_ClassAB_Open>',text)
 assert re.search(r'\bbl\s+0x[0-9a-f]+ <Speaker_ClassAB_close>',text)
 checks.append(f'{label}: unchanged public instruction bytes in ELF wrapper; actual ClassAB open/close calls remain')
s=(ROOT/'evidence/stock-public-disassembly.txt').read_text();sect=s[s.index('<Ext_Speaker_Amp_Set>:'):s.index('<Speaker_Amp_Change>:')]
assert '<gpiod_set_raw_value>' in sect and '<AudDrv_GPIO_EXTAMP_Select>' not in sect and '<__udelay>' not in sect
s=(ROOT/'evidence/bmc-disassembly.txt').read_text();sect=s[s.index('<Ext_Speaker_Amp_Set>:'):s.index('<Speaker_Amp_Change>:')]
assert len(re.findall(r'\bbl\s+0x[0-9a-f]+ <AudDrv_GPIO_EXTAMP_Select>',sect))==8
checks.append('Actual stock external setter reaches gpio raw high/low, no AW pulse boundary; actual combined setter has eight EXTAMP select call sites')
stock=fdt((ROOT/'inputs/stock-public/appended.dtb').read_bytes());bmc=fdt((ROOT/'inputs/bmc/asus-p00a.dtb').read_bytes())
assert stock['/soc/mt_soc_codec_name@11220000']['extspkamp-gpio']==struct.pack('>III',13,28,0)
assert 'extspkamp-gpio' not in bmc['/soc/mt_soc_codec_name@11220000']
assert not any('switch-mode-delay' in v for v in bmc.values())
checks.append('Actual stock DT names GPIO28; combined DT omits it and required delay property')
run(['python3',ROOT/'scripts/host_checks.py'],output='evidence/host-replay.txt')
checks.append('Five host fragment variants passed; counterfactual AW-off has no external pulses, internal preprocessed function equal; stock GPIO28 missing from counterfactual')
assert not list((ROOT/'proposal').glob('*.patch'))
(ROOT/'evidence/final-verification.json').write_text(json.dumps({'status':'PASS bounded offline evidence; BRANCH BLOCKER for fitted-topology implementation','checks':checks,'source_config_delta':[],'route_qualified':False,'physical_flash_GO':False,'PCM_callback_work_performed':False,'device_operations':0,'network_operations':0,'target_builds':0},indent=2)+'\n')
print('\n'.join(checks))
