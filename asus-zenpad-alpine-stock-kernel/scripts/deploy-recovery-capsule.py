#!/usr/bin/env python3
"""Guarded recovery-only RAM capsule staging; default is an offline plan."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shlex, subprocess
HERE=Path(__file__).resolve().parents[1]
STOCK=HERE.parent/'2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback'
HELPER=HERE.parent/'2026-11-07-asus-usb-retained-log-collector/scripts/root_shell_usb.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
BOOT='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
REC='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args()
    manifest=json.loads((HERE/'artifacts/recovery-capsule/manifest.json').read_text())
    candidate=HERE/'artifacts/recovery-capsule'/manifest['image_file'];image=candidate.read_bytes()
    assert len(image)==16740352 and sha(image)==manifest['image_sha256']
    assert manifest['kernel_byte_identical_to_original_boot'] and manifest['kernel_byte_identical_to_original_recovery']
    assert manifest['kernel_wrapped_sha256']=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
    assert sha((STOCK/'boot.img').read_bytes())==BOOT and sha((STOCK/'recovery.img').read_bytes())==REC
    before=(HERE/'private/live/bcb.preflight.bin').read_bytes();clean=(HERE/'private/live/bcb.clear-stale-recovery.bin').read_bytes()
    assert len(before)==len(clean)==2048 and before[:32]==bytes(32)
    assert before[64:832].split(b'\0',1)[0]==b'recovery\n--wipe_data'
    assert clean==before[:64]+bytes(768)+before[832:]
    plan={'operation':'recovery-slot RAM boot capsule and removal of stale recovery request','candidate_sha256':sha(image),'recovery_rollback_sha256':REC,'bcb_before_sha256':sha(before),'bcb_clean_sha256':sha(clean),'writes':[{'partition':'para','offset':0,'bytes':2048,'changes':'only recovery argument field'},{'partition':'recovery','offset':0,'bytes':len(image)}],'normal_boot_system_data_gpt_bootloader_factory_unchanged':True,'reboot':False}
    (HERE/'evidence/recovery-deployment-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if not a.execute:print(json.dumps({'status':'OFFLINE_PLAN_ONLY',**plan},indent=2));return
    spec=importlib.util.spec_from_file_location('root_guard',HELPER);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    assert guard.query(['get-serialno'])==guard.SERIAL
    for prop,expected in guard.PROPS.items():assert guard.query(['shell','getprop',prop])==expected
    assert guard.query(['shell','getenforce'])=='Enforcing'
    boot_id=guard.query(['shell','cat','/proc/sys/kernel/random/boot_id'])
    files=[(candidate,'/data/local/tmp/asus-alpine-capsule.img'),(STOCK/'recovery.img','/data/local/tmp/asus-alpine-stock-recovery.img'),(HERE/'private/live/bcb.clear-stale-recovery.bin','/data/local/tmp/asus-alpine-bcb.clean.bin')]
    for source,target in files:subprocess.run(guard.ADB+['push',str(source),target],check=True,capture_output=True,timeout=30)
    script='''R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ "$(cat /proc/sys/kernel/random/boot_id)" = @BOOT_ID@ ]
[ "$(getprop init.svc.flash_recovery)" = stopped ]
P=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name
[ "$(readlink -f "$P/recovery")" = /dev/block/mmcblk0p10 ]
[ "$(readlink -f "$P/para")" = /dev/block/mmcblk0p12 ]
[ "$(cat /sys/class/block/mmcblk0p10/start)" = 160184 ]
[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32696 ]
[ "$(cat /sys/class/block/mmcblk0p12/start)" = 225576 ]
[ "$(cat /sys/class/block/mmcblk0p12/size)" = 1024 ]
[ "$(stat -c %s /data/local/tmp/asus-alpine-capsule.img)" = 16740352 ]
[ "$(stat -c %s /data/local/tmp/asus-alpine-bcb.clean.bin)" = 2048 ]
digest() { chroot "$R" /bin/busybox sha256sum < "$1" | cut -d ' ' -f 1; }
[ "$(digest /data/local/tmp/asus-alpine-capsule.img)" = @CANDIDATE@ ]
[ "$(digest /data/local/tmp/asus-alpine-stock-recovery.img)" = @RECOVERY@ ]
[ "$(digest /data/local/tmp/asus-alpine-bcb.clean.bin)" = @BCB_CLEAN@ ]
[ "$(digest "$P/boot")" = @BOOT@ ]
[ "$(digest "$P/recovery")" = @RECOVERY@ ]
dd if="$P/para" of="$R/tmp/bcb-before-deployment.bin" bs=2048 count=1 2>/dev/null
[ "$(digest "$R/tmp/bcb-before-deployment.bin")" = @BCB_BEFORE@ ]
cat /system/bin/install-recovery.sh
# First neutralize only the backed-up stale recovery argument field.
dd if=/data/local/tmp/asus-alpine-bcb.clean.bin of="$P/para" bs=2048 count=1 2>/dev/null
sync
dd if="$P/para" of="$R/tmp/bcb-after-deployment.bin" bs=2048 count=1 2>/dev/null
[ "$(digest "$R/tmp/bcb-after-deployment.bin")" = @BCB_CLEAN@ ]
restore_stock_recovery() {
 dd if=/data/local/tmp/asus-alpine-stock-recovery.img of="$P/recovery" bs=1048576 2>/dev/null || return 1
 sync
 [ "$(digest "$P/recovery")" = @RECOVERY@ ]
}
if ! dd if=/data/local/tmp/asus-alpine-capsule.img of="$P/recovery" bs=1048576 2>/dev/null; then
 restore_stock_recovery || { echo ROLLBACK_FAILED; exit 98; }
 echo WRITE_FAILED_STOCK_RECOVERY_RESTORED; exit 97
fi
sync
if [ "$(digest "$P/recovery")" != @CANDIDATE@ ]; then
 restore_stock_recovery || { echo ROLLBACK_FAILED; exit 98; }
 echo READBACK_FAILED_STOCK_RECOVERY_RESTORED; exit 97
fi
[ "$(digest "$P/boot")" = @BOOT@ ]
echo CAPSULE_INSTALLED_READBACK_PASS=@CANDIDATE@
echo BCB_STALE_REQUEST_CLEARED=@BCB_CLEAN@
'''
    values={'BOOT_ID':boot_id,'CANDIDATE':sha(image),'RECOVERY':REC,'BCB_CLEAN':sha(clean),'BCB_BEFORE':sha(before),'BOOT':BOOT}
    for key,value in values.items():script=script.replace('@'+key+'@',shlex.quote(value))
    (HERE/'private/live/recovery-deployment-script.sh').write_text(script)
    result=subprocess.run(['python3',str(HELPER)],input=script,text=True,capture_output=True,timeout=90,cwd=HERE)
    (HERE/'private/live/recovery-deployment.txt').write_text(result.stdout)
    (HERE/'private/live/recovery-deployment.stderr').write_text(result.stderr)
    assert result.returncode==0,(result.returncode,'see private deployment logs')
    assert 'CAPSULE_INSTALLED_READBACK_PASS='+sha(image) in result.stdout
    assert guard.query(['shell','getenforce'])=='Enforcing'
    receipt={'status':'DEPLOYED_READBACK_VERIFIED_NOT_BOOTED',**plan}
    (HERE/'evidence/recovery-deployment-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
