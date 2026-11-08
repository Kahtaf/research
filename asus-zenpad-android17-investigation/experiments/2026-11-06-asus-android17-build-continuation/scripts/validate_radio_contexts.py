#!/usr/bin/env python3
import pathlib,subprocess,json,shlex,hashlib,shutil,sys
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');D=R/'product-device';O=R/('context-validation-'+sys.argv[1]);O.mkdir();pins={};records=[]
def freeze(p):
    q=O/'inputs'/str(p).lstrip('/');q.parent.mkdir(parents=True,exist_ok=True)
    h=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copyfile(p,q)
    assert h==hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(q.read_bytes()).hexdigest();pins[str(p)]=h
    return q
def run(args,expected=0):
    p=subprocess.run(list(map(str,args)),capture_output=True);records.append({'argv':list(map(str,args)),'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()})
    (O/'results.json').write_text(json.dumps({'inputs':pins,'commands':records},indent=2)+'\n')
    assert (p.returncode==0)==(expected==0),records[-1]
    return p.stdout
rules=json.loads((R/'policy-tools-r1/property-context-rules.json').read_text())
cmd=shlex.split(rules['rule m.vendor_property_contexts_android_common.selinux_contexts'])
start=cmd.index('prebuilts/build-tools/linux-x86/bin/m4');stop=cmd.index('system/sepolicy/flagging/flagging_macros')
flags=cmd[start+1:stop];macros=freeze(A/'system/sepolicy/flagging/flagging_macros')
sets={
    'plat':[A/'system/sepolicy/private/property_contexts'],
    'system_ext':[A/'device/lineage/sepolicy/common/private/property_contexts'],
    'vendor':[A/'system/sepolicy/vendor/property_contexts',A/'device/lineage/sepolicy/common/vendor/property_contexts',A/'system/sepolicy/reqd_mask/property_contexts',D/'radio/sepolicy/property_contexts'],
}
contexts=[]
for name,sources in sets.items():
    newline=O/'newline';newline.write_text('\n');inputs=[]
    for p in sources:inputs.extend([freeze(p),newline])
    data=run([A/'prebuilts/build-tools/linux-x86/bin/m4',*flags,macros,*inputs]);q=O/(name+'_property_contexts');q.write_bytes(data);contexts.append(q)
policy=freeze(R/'policy-merge-r3/policy.bin');checker=R/'property-tools-r1/property_info_checker'
run([checker,policy,*contexts])
bad=O/'invalid-property-contexts';bad.write_text('vendor.p00a.invalid u:object_r:p00a_radio_device:s0 exact bool\n');run([checker,policy,bad],expected=1)
fc=freeze(D/'radio/sepolicy/file_contexts');run([R/'policy-tools-r1/checkfc',policy,fc])
cases={'/vendor/bin/p00a-wmt':'p00a_radio_exec','/system/vendor/bin/p00a-wmt':'p00a_radio_exec','/dev/stpbt':'p00a_stpbt_device','/dev/wmtdetect':'p00a_radio_device','/dev/socket/p00a_wmt_ready':'p00a_radio_socket','/data/vendor/p00a/nvram/APCFG/APRDEB/BT_Addr':'p00a_radio_nvram_file','/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI':'p00a_radio_nvram_file','/data/vendor/bluetooth/p00a/bdaddr':'p00a_bt_address_file','/vendor/bin/hw/android.hardware.bluetooth@1.1-service.p00a':'hal_bluetooth_default_exec'}
for name in ['WMT_SOC.cfg','WIFI_RAM_CODE_8163','ROMv2_lm_patch_1_0_hdr.bin','ROMv2_lm_patch_1_1_hdr.bin']:cases['/vendor/firmware/'+name]='p00a_radio_firmware_file'
for path in ['/data/vendor/p00a','/data/vendor/p00a/nvram','/data/vendor/p00a/nvram/APCFG','/data/vendor/p00a/nvram/APCFG/APRDEB']:cases[path]='p00a_radio_nvram_file'
for path in ['/dev/stpwmt','/dev/wmtWifi']:cases[path]='p00a_radio_device'
test=O/'file-label-cases';test.write_text(''.join(f'{p} {label}\n' for p,label in cases.items()));run([R/'policy-tools-r1/checkfc','-t',fc,test])
for p in ['radio/init.p00a-radio.rc','radio/bluetooth-p00a.rc','radio/wificond.rc']:
    run([A/'out/host/linux-x86/bin/host_init_verifier',*[f'--property-contexts={x}' for x in contexts],freeze(D/p)])
print('Combined property contexts, negative property type,',len(cases),'file labels and 3 init scripts PASS')
