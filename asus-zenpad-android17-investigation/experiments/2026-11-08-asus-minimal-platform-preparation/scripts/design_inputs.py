from pathlib import Path
import json,re,difflib
R=Path(__file__).resolve().parents[1]
base=(R/'config/baseline.config').read_text()
# Whole nonessential consumer classes; retain the vendor protection dependency closure.
disable='''ANDROID_DEFAULT_SETTING NOP_USB_XCEIV DUAL_ROLE_USB_INTF NET NETDEVICES WIRELESS WLAN CFG80211 BT INET BRIDGE NETFILTER
MTK_GPT_SCHEME_SUPPORT MTK_VIDEOCODEC_DRIVER MTK_CAMERA_ISP MTK_M4U MTK_SMI_EXT MTK_SMI_VARIANT MTK_CMDQ_TAB MTK_JPEG MTK_LCM MTK_SYNC MTK_FB MTK_VIDEOX
MTK_SENSOR_SUPPORT MTK_HWMON MTK_SENSORS_1_0 MTK_LTR559 MTK_CCCI_DEVICES MTK_COMBO MTK_COMBO_BT MTK_COMBO_WIFI MTK_GPS ASUS_P00A_RADIO MTK_BTIF MTK_BTCVSD
MTK_ACCDET MTK_LEDS ASUS_P00A_LP8557 MTK_PWM MTK_GPU_SUPPORT MTK_GPU_COMMON_DVFS_SUPPORT
USB_MTK_HDRC MTK_MUSB_QMU_SUPPORT USB_MTK_OTG MTK_USBFSH USB_SUPPORT USB_GADGET USB USB_PHY
SOUND MEDIA_SUPPORT FB BACKLIGHT_LCD_SUPPORT HID RC_CORE
MMC MMC_MTK SCSI ATA MTD BLK_DEV_MD BLK_DEV_DM BLK_DEV_LOOP BLK_DEV_RAM BLK_DEV_NBD
INPUT_TOUCHSCREEN TOUCHSCREEN_GOODIX INPUT_HALL_BU520 INPUT_JOYSTICK INPUT_UINPUT
MTK_ION ION FTRACE EXT4_FS F2FS_FS VFAT_FS FAT_FS MSDOS_FS NTFS_FS SQUASHFS OVERLAY_FS FUSE_FS ECRYPT_FS
MTK_SEC_VIDEO_PATH_SUPPORT MTK_IN_HOUSE_TEE_SUPPORT MTK_SSMR'''.split()
existing=set(re.findall(r'^(?:# )?CONFIG_(\w+)(?:=| is not set)',base,re.M))
request={x:'n' for x in disable if x in existing}
request['CMDLINE']='"androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 nr_cpus=1"'
# Do not force NR_CPUS=1: the actual arm64 Kconfig range begins at 2.
lines=[]
for line in base.splitlines():
 m=re.match(r'^(?:# )?CONFIG_(\w+)(?:=| is not set)',line)
 if m and m[1] in request:
  name=m[1];v=request[name];line='# CONFIG_'+name+' is not set' if v=='n' else 'CONFIG_'+name+'='+v
 lines.append(line)
(R/'config/requested.config').write_text('\n'.join(lines)+'\n')
(R/'config/intent.json').write_text(json.dumps(dict(request=request,not_present=[x for x in disable if x not in existing],keeper_policy='all other baseline values supplied to olddefconfig; derived closure recorded separately'),indent=2)+'\n')
# Append status-only overrides; all address, reservation, supply, trip and clock properties stay intact.
classes={
'USB':['/soc/usb@11200000','/soc/usb@11270000'],
'MMC':['/soc/mmc@11230000','/soc/mmc@11240000','/soc/mmc@11250000'],
'display':['/lcm','/soc/mtkfb@0','/soc/mt8163-dispsys','/soc/hdmi@1401d000','/soc/disp_ovl0@14007000','/soc/disp_ovl1@14008000','/soc/disp_rdma0@14009000','/soc/disp_rdma1@1400a000','/soc/disp_wdma0@1400b000','/soc/disp_wdma1@14018000','/soc/disp_color@1400c000','/soc/disp_ccorr@1400d000','/soc/disp_aal@1400e000','/soc/disp_gamma@1400f000','/soc/disp_dither@14010000','/soc/disp_ufoe@14011000','/soc/disp_dsi0@14012000','/soc/disp_dpi0@14013000','/soc/disp_dpi1@1401c000','/soc/disp_pwm0@14014000','/soc/disp_lvds_tx@1401b200','/soc/i2c@11007000/lp8557_led@2c'],
'media-camera':['/soc/gce@10212000','/soc/mdp_rdma@14001000','/soc/mdp_rsz0@14002000','/soc/mdp_rsz1@14003000','/soc/mdp_wdma@14004000','/soc/mdp_wrot@14005000','/soc/mdp_tdshp@14006000','/soc/ispsys@15000000','/soc/isp_display','/soc/camera1@15008000','/soc/camera2@15008000','/soc/vdec@16020000','/soc/venc@17002000','/soc/jpgenc@17003000','/soc/isp_pipemgr','/soc/isp_sysram','/soc/flashlight@'],
'sensors-touch':['/cust_accel@0','/cust_mag@0','/hall_sensor','/soc/i2c@11009000','/soc/i2c@11007000/elan@10','/soc/i2c@11007000/goodix@14','/soc/touch@','/soc/hwmsensor@0','/soc/gsensor@0','/soc/als_ps@0','/soc/batchsensor@0','/soc/gyroscope@0','/soc/barometer@0','/soc/msensor@0','/soc/orientation@0'],
'network':['/soc/consys@18070000','/soc/wifi@180f0000','/soc/gps','/soc/btif@1100c000','/soc/btif_tx@11000700','/soc/btif_rx@11000780','/soc/btcvsd@18000000'],
'other-consumers':['/soc/accdet@','/soc/pwm@11006000','/soc/nfi@1100d000','/soc/nfiecc@1100e000','/soc/dumchar']}
# Audio DT endpoints are flat siblings. Identify only explicit audio consumer nodes.
soc=(R/'source/baseline/arch/arm64/boot/dts/mediatek/mt8163.dtsi').read_text()
audio=re.findall(r'^\t\t(?:\w+:\s*)?(mt_soc_[\w@]+)\s*\{',soc,re.M)
classes['audio']=['/soc/'+n for n in audio]+['/soc/accdet@']
# Keep audiosys clock provider, mmsys/imgsys/vdec/venc clock providers, all rail nodes.
classes['other-consumers'].remove('/soc/accdet@')
manifest=[dict(path=p,device_class=c,reason='No RAM PID1 function; class driver disabled in config; status prevents ordinary OF population/probe') for c,ps in classes.items() for p in ps]
paths=[x['path'] for x in manifest];assert len(paths)==len(set(paths))
# &{/path} references fail DT compilation if a named node does not exist; never create a new path.
fragment='\n/* One RAM-only consumer removal set. Keep all providers and protection nodes. */\n'
fragment+='\n'.join('&{'+p+'} { status = "disabled"; };' for p in paths)+'\n'
p='arch/arm64/boot/dts/mediatek/asus-p00a.dts'
b=(R/'source/baseline'/p).read_text()
# Replace only chosen bootargs. Packaging must preserve these selected arguments.
b=b.replace('console=ttyMT0,921600n1 root=/dev/ram','androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 nr_cpus=1')
q=R/'source/proposed'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(b+fragment)
(R/'dt/status-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Remove the five legacy setup/IRQ/time checkpoints; retained writer/entry geometry untouched.
p='init/main.c';s=(R/'source/baseline'/p).read_text()
s='\n'.join(l for l in s.split('\n') if 'asus_retained_trace_mark(' not in l and '#include <linux/asus_retained_trace.h>' not in l)
q=R/'source/proposed'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s)
print('One configuration request and status-only DT delta prepared.')
