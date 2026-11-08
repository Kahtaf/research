from pathlib import Path
import re,hashlib,json,datetime
base=Path(__file__).resolve().parents[2];spike=Path(__file__).resolve().parents[1]
stock=base/'2026-11-05-asus-latest-android-feasibility/sources';kernel=stock/'asus-original/kernel-3.18'
checks={
 kernel/'arch/arm64/configs/asus8163_tb_380_m_defconfig':r'CONFIG_.*(CUSTOM_KERNEL_IMGSENSOR|MTK_IMGSENSOR|BMC156|AP3425|CUSTOM_KERNEL_ACCEL|CUSTOM_KERNEL_MAG|CUSTOM_KERNEL_ALS|MT_SND_SOC)',
 kernel/'drivers/misc/mediatek/accelerometer/bmc156_acc/bmc156_acc.c':r'GS_CALI_PATH|filp_open\(GS|compatible|GSENSOR_IOCTL_(GET|SET)_CALI',
 kernel/'drivers/misc/mediatek/alsps/ap3425h/ap3xx6c.c':r'ALS_CALI_PATH|filp_open\(ALS|compatible|AP3425H_CALI_FILE_LENGTH',
 kernel/'drivers/input/touchscreen/mediatek/gt6108/gt6108.h':r'GTP_COMPATIBLE_MODE|GTP_BAK_REF_PATH|GTP_MAIN_CLK_PATH',
 kernel/'drivers/input/touchscreen/mediatek/gt6108/gt6108_asus.c':r'UPDATE_FILE_PATH',
 kernel/'drivers/input/touchscreen/mediatek/gt6108/gt6108_openshort.c':r'define TEST_CONFIG_FILE_PATH',
 kernel/'drivers/input/touchscreen/mediatek/gt6108/gt6108_update.c':r'define.*(UPDATE_FILE_PATH|CONFIG_FILE_PATH)',
 kernel/'drivers/misc/mediatek/accelerometer/accel.c':r'input_report_|accdevnum|devname =',
 stock/'stock-firmware/ramdisk/fstab.mt8163':r'by-name/(userdata|persist|nvram|proinfo)',
 stock/'stock-firmware/ramdisk/init.mt8163.rc':r'/data/nvram|/data/misc/(sensor|akmd|acdapi)|/persist|bmm050d|start bmm|/dev/gsensor|/dev/msensor',
}
out=[]
for p,pattern in checks.items():
 out+=['\nFILE '+str(p.relative_to(base))+' SHA256 '+hashlib.sha256(p.read_bytes()).hexdigest()]
 out += [f'{i}: {l}' for i,l in enumerate(p.read_text(errors='replace').splitlines(),1) if re.search(pattern,l)]
(spike/'evidence/local-public-source.txt').write_text('\n'.join(out)+'\n')
# Only subsystem fact lines from the prior hardware baseline; no user metadata copied.
p=base/'2026-11-05-asus-root-hardware-validation/evidence/stock-hardware-baseline-raw.txt'
lines=p.read_text(errors='replace').splitlines()
facts=[f'{i}: {l}' for i,l in enumerate(lines,1) if re.search(r'^0x[0-9a-f]+\) (ACCELEROMETER|MAGNETOMETER|LIGHT|ORIENTATION)|^\s+name:.*goodix|ConfigurationFile:.*goodix|KeyLayoutFile:.*goodix',l)]
(spike/'evidence/prior-stock-hardware-facts.txt').write_text('Source: '+str(p.relative_to(base))+'\nFiltered hardware facts only; historical Android7 evidence, not Android17 qualification.\n'+'\n'.join(facts)+'\n')
print('Captured',len(out),'public source lines and',len(facts),'hardware facts')
