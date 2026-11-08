#!/usr/bin/env python3
import hashlib,json,struct,sys,zlib
from pathlib import Path
base=Path('/srv/android/asus-android17')
out=Path(sys.argv[2]) if len(sys.argv)>2 else base/('build-main-battery-soc-'+sys.argv[1])
record=Path('/srv/android/asus-build-continuation/logs')/('kernel-'+sys.argv[1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(p):
 data=p.read_bytes();z=zlib.decompressobj(31);z.decompress(data);dt=z.unused_data
 assert dt[:4]==bytes.fromhex('d00dfeed'),'No appended FDT'
 size=struct.unpack_from('>I',dt,4)[0];assert size==len(dt),'Multiple/trailing DT bytes'
 return dt
def parse(b):
 h=struct.unpack_from('>10I',b);pos=h[2];strings=b[h[3]:h[3]+h[8]];stack=[];nodes={}
 while True:
  t=struct.unpack_from('>I',b,pos)[0];pos+=4
  if t==1:
   end=b.index(0,pos);stack.append(b[pos:end].decode());pos=(end+4)&~3;nodes['/'.join(stack)]={}
  elif t==2:stack.pop()
  elif t==3:
   n,off=struct.unpack_from('>II',b,pos);pos+=8;name=strings[off:strings.index(0,off)].decode();nodes['/'.join(stack)][name]=b[pos:pos+n];pos=(pos+n+3)&~3
  elif t==4:continue
  elif t==9:break
  else:raise ValueError(t)
 return nodes
image=out/'arch/arm64/boot/Image.gz-dtb';dt=extract(image);old=extract(base/'build-bpf-fd/arch/arm64/boot/Image.gz-dtb')
nodes=parse(dt);old_nodes=parse(old)
dt_changes=[]
allowed={'isense_channel_number':7,'rbat_pull_down_r':30000,'swchr_power_path':1,'vbat_channel_number':6,'vbattemp_channel_number':5,'vcharger_channel_number':4}
for n in set(nodes)|set(old_nodes):
 for key in set(nodes.get(n,{}))|set(old_nodes.get(n,{})):
  x=nodes.get(n,{}).get(key);y=old_nodes.get(n,{}).get(key)
  if x!=y:
   if n=='/chosen' and key=='bootargs':
    assert x==y.replace(b' initrd=0x44000200,0x200000',b'')
    dt_changes.append(dict(node=n,property=key,old=y.decode(),new=x.decode()))
    continue
   assert n=='/soc/bat_meter' and key in allowed and y is None and x==struct.pack('>I',allowed[key]),(n,key)
   dt_changes.append(dict(node=n,property=key,old=None,new=allowed[key]))
assert not any('asus,allow-battery-charging' in props for props in nodes.values())
batteries=[(n,p) for n,p in nodes.items() if 'battery_profile_t0' in p];assert len(batteries)==1
node,props=batteries[0]
def cells(name):
 b=props[name];assert len(b)%4==0;return list(struct.unpack('>'+str(len(b)//4)+'I',b))
expected={'vbat_channel_number':6,'isense_channel_number':7,'vcharger_channel_number':4,'vbattemp_channel_number':5,'swchr_power_path':1,'temperature_t0':110,'temperature_t1':0,'temperature_t2':25,'temperature_t3':50,'oam_d5':0}
for name,n in expected.items():assert cells(name)==[n],(name,cells(name))
assert cells('rbat_pull_up_r')==[16900]
assert cells('rbat_pull_up_volt')==[1800]
assert cells('rbat_pull_down_r')==[30000]
profiles={}
for prefix in ['battery_profile','r_profile']:
 for i in range(4):
  n=f'{prefix}_t{i}';assert cells(n+'_num')==[104];assert len(cells(n))==208;profiles[n]=dict(pairs=104,sha256=hashlib.sha256(props[n]).hexdigest())
config=(out/'.config').read_text().splitlines()
for n in ['ASUS_P00A_MAIN_BATTERY_SOC','ASUS_P00A_BATTERY_DIAGNOSTIC','ASUS_P00A_BQ25896','MTK_SMART_BATTERY','MTK_PMIC','OF','ASUS_P00A_RADIO','MTK_COMBO','MTK_BTIF','CFG80211','USB_CONFIGFS','USB_CONFIGFS_F_FS']:assert f'CONFIG_{n}=y' in config,n
for n in ['MTK_MULTI_BAT_PROFILE_SUPPORT','MTK_BATTERY_LIFETIME_DATA_SUPPORT','POWER_EXT']:assert f'CONFIG_{n}=y' not in config,n
objects=[]
for n in ['battery_meter.o','battery_common.o','battery_diag.o','pmic_mt6323.o','mtk_ts_battery.o']:
 matches=list(out.rglob(n));assert len(matches)==1,(n,matches);objects.append(dict(path=str(matches[0]),sha256=sha(matches[0]),bytes=matches[0].stat().st_size))
r=dict(image=dict(path=str(image),sha256=sha(image),bytes=image.stat().st_size),config_sha256=sha(out/'.config'),dtb_sha256=hashlib.sha256(dt).hexdigest(),dtb_matches_original=dt==old,reviewed_dt_changes=dt_changes,charging_opt_in_absent=True,battery_node=node,settings={n:cells(n) for n in props if any(s in n for s in ['channel','q_max','pull_up','pull_down','swchr'])},profiles=profiles,compiled_objects=objects,hardware_validated=False)
Path(str(record)+'.dtb').write_bytes(dt)
Path(str(record)+'.evidence.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
