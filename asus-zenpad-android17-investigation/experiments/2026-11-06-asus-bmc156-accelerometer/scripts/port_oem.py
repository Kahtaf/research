from pathlib import Path
import hashlib,json,difflib
S=Path(__file__).resolve().parents[1]; O=S.parent/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/drivers/misc/mediatek/accelerometer/bmc156_acc'
s=(O/'bmc156_acc.c').read_text(); assert hashlib.sha256(s.encode()).hexdigest()=='d3a43a00419e7c1096e1b216ae665a57a69e7af3ab0ff363240e4aed14a9a609'
D=S/'source/kernel/drivers/misc/mediatek/sensors-1.0/accelerometer/bmc156_acc';D.mkdir(parents=True,exist_ok=True)
P=S/'source/oem-preimages';P.mkdir(exist_ok=True)
for n in ['bmc156_acc.c','bmc156_acc.h','Kconfig','Makefile']:(P/n).write_bytes((O/n).read_bytes())
(D/'bmc156_acc.h').write_bytes((O/'bmc156_acc.h').read_bytes())
def func(name):
 start=s.index('static int '+name+'('); end=s.index('\n}',start)+2
 return s[start:end]+'\n'
head=s[:s.index('#include <linux/interrupt.h>')]
head+='''/* Accelerometer-only P00A adaptation of this exact OEM driver.
 * Sensorhub, diagnostic FIFO, factory writes and legacy misc ABI are omitted.
 */
#include <linux/i2c.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/pm.h>
#include <asm/unaligned.h>
#include <accel.h>
#include <cust_acc.h>
#include <hwmsen_helper.h>
#include "bmc156_acc.h"

#define BMA255_AXIS_X 0
#define BMA255_AXIS_Y 1
#define BMA255_AXIS_Z 2
#define BMA255_AXES_NUM 3
#define BMA255_DATA_LEN 6
#define BMA255_MODE_NORMAL 0
#define BMA255_MODE_SUSPEND 2
#define GSE_ERR(fmt, ...) pr_err("bmc156_acc: " fmt, ##__VA_ARGS__)
#define GSE_LOG(fmt, ...) pr_debug("bmc156_acc: " fmt, ##__VA_ARGS__)
'''
head+=s[s.index('#define BMA255_ACC_X_LSB__POS'):s.index('/*----------------------------------------------------------------------------*/',s.index('#define BMA255_GET_BITSLICE'))]
head+='''
struct data_resolution { int sensitivity; };
static struct data_resolution bma255_data_resolution[] = {{512}};
struct bma255_i2c_data {
 struct i2c_client *client;
 struct acc_hw hw;
 struct hwmsen_convert cvt;
 struct data_resolution *reso;
 struct mutex lock;
 s16 cali_sw[3];
 bool calibrated;
 bool suspended;
 bool requested;
 u8 bandwidth;
};
static struct bma255_i2c_data *obj_i2c_data;
static bool sensor_power = true;
static bool sensor_power_valid;
static DEFINE_MUTEX(i2c_lock);
static DEFINE_MUTEX(operation_lock);
static int bma255_init_flag = -ENODEV;
'''
rd=func('bma_i2c_read_block');rd=rd.replace('#ifdef CONFIG_I2C_BASIC_FUNCTION\n','').split('#else')[0]+'}\n'
wr=func('bma_i2c_write_block');wr=wr.replace('#ifdef CONFIG_I2C_BASIC_FUNCTION\n','').split('#else')[0]+'}\n'
wr=wr.replace('if (err < 0) {','if (err != num) {')
wr=wr.replace('if (!client)\n\t\treturn -EINVAL;','if (!client || len > 31)\n\t\treturn -EINVAL;')
res='''static int BMA255_SetDataResolution(struct bma255_i2c_data *obj)
{
 obj->reso = &bma255_data_resolution[0];
 return 0;
}
'''
raw=func('BMA255_ReadData');start=raw.index('#ifdef CONFIG_BMA255_LOWPASS');end=raw.index('#endif',start)+len('#endif');raw=raw[:start]+raw[end:]
raw=raw.replace('err = -EINVAL;','return -EINVAL;')
reg=''.join(func(n) for n in ['BMA255_CheckDeviceID','BMA255_SetPowerMode','BMA255_SetDataFormat','BMA255_SetBWRate','BMA255_SetIntEnable'])
# Do not follow failed reads with register writes, and don't mask first ID read errors.
reg=reg.replace('res = bma_i2c_read_block(client, BMA255_REG_DEVID, databuf, 0x01);\n\tres =', 'res =')
reg=reg.replace('res += bma_i2c_read_block(client,\n\t\tBMA255_LOW_POWER_CTRL_REG, &databuf[1], 1);','if (!res)\n\t\tres = bma_i2c_read_block(client,\n\t\t\tBMA255_LOW_POWER_CTRL_REG, &databuf[1], 1);\n\tif (res) {\n\t\tmutex_unlock(&obj->lock);\n\t\treturn res;\n\t}')
for token in ['BMA255_RANGE_SEL_REG','BMA255_BANDWIDTH__REG']:
 needle=f'{token}, &databuf[0], 1);'
 reg=reg.replace(needle,needle+'\n\tif (res) {\n\t\tmutex_unlock(&obj->lock);\n\t\treturn res;\n\t}',1)
reg=reg.replace('if (enable == sensor_power) {', 'if (sensor_power_valid && enable == sensor_power) {')
reg=reg.replace('GSE_ERR("set power mode failed, res = %d\\n", res);', 'sensor_power_valid = false;\n\t\tGSE_ERR("set power mode failed, res = %d\\n", res);')
reg=reg.replace('sensor_power = enable;', 'sensor_power = enable;\n\tsensor_power_valid = true;')
body='''
static int bmc156_init_client(struct bma255_i2c_data *obj)
{
 int err;
 err = BMA255_CheckDeviceID(obj->client);
 if (err) return err;
 err = BMA255_SetBWRate(obj->client, obj->bandwidth);
 if (err) return err;
 err = BMA255_SetDataFormat(obj->client, BMA255_RANGE_4G);
 if (err) return err;
 err = BMA255_SetIntEnable(obj->client, 0);
 if (err) return err;
 /* Force a real suspend transition at probe; no board LDO is controllable. */
 sensor_power_valid = false;
 err = BMA255_SetPowerMode(obj->client, obj->requested);
 mdelay(20);
 return err;
}

static int bmc156_enable(int en)
{
 int err;
 struct bma255_i2c_data *obj = obj_i2c_data;
 if (!obj || (en != 0 && en != 1)) return -EINVAL;
 mutex_lock(&operation_lock);
 if (obj->suspended) err = -EBUSY;
 else {
  err = BMA255_SetPowerMode(obj->client, en);
  if (!err) obj->requested = en;
 }
 mutex_unlock(&operation_lock);
 return err;
}

static int bmc156_batch(int flag, int64_t ns, int64_t latency)
{
 struct bma255_i2c_data *obj = obj_i2c_data;
 int err;
 u8 bw;
 if (!obj || flag || latency || ns < 10000000 || ns > 200000000) return -EINVAL;
 bw = ns <= 10000000 ? BMA255_BW_100HZ : BMA255_BW_50HZ;
 mutex_lock(&operation_lock);
 if (obj->suspended) err = -EBUSY;
 else {
  err = BMA255_SetBWRate(obj->client, bw);
  if (!err) obj->bandwidth = bw;
 }
 mutex_unlock(&operation_lock);
 return err;
}

static int bmc156_get_data(int *x, int *y, int *z, int *status)
{
 struct bma255_i2c_data *obj = obj_i2c_data;
 s16 raw[3];
 int board[3], i, err;
 if (!obj) return -ENODEV;
 mutex_lock(&operation_lock);
 if (!sensor_power_valid) { err = -EIO; goto out; }
 if (obj->suspended || !sensor_power) { err = -EAGAIN; goto out; }
 err = BMA255_ReadData(obj->client, raw);
 if (err) goto out;
 /* Same OEM calibration-before-map and integer scale order. */
 for (i = 0; i < 3; ++i)
  board[obj->cvt.map[i]] = obj->cvt.sign[i] * (raw[i] + obj->cali_sw[i])
                          * GRAVITY_EARTH_1000 / obj->reso->sensitivity;
 *x = board[0]; *y = board[1]; *z = board[2];
 *status = obj->calibrated ? SENSOR_STATUS_ACCURACY_MEDIUM : SENSOR_STATUS_UNRELIABLE;
out:
 mutex_unlock(&operation_lock);
 return err;
}

/* Absolute board-coordinate raw counts; never add twice on HAL reopen. */
static int bmc156_set_cali(uint8_t *data, uint8_t count)
{
 struct bma255_i2c_data *obj = obj_i2c_data;
 s32 cal[3];
 int i;
 if (!obj || count != 12) return -EINVAL;
 for (i = 0; i < 3; ++i) {
  cal[i] = (s32)get_unaligned_le32(data + 4*i);
  /* Exact acceptance bound in OEM bma_do_cali. */
  if (cal[i] < -250 || cal[i] > 250) return -ERANGE;
 }
 mutex_lock(&operation_lock);
 if (!sensor_power_valid) {
  mutex_unlock(&operation_lock); return -EIO;
 }
 if (sensor_power || obj->suspended) {
  mutex_unlock(&operation_lock); return -EBUSY;
 }
 for (i = 0; i < 3; ++i)
  obj->cali_sw[i] = obj->cvt.sign[i] * cal[obj->cvt.map[i]];
 obj->calibrated = true;
 mutex_unlock(&operation_lock);
 return 0;
}

static int bmc156_flush(void)
{
 int err = acc_flush_report();
 return err == -1 ? -ENOSPC : err;
}
static int bmc156_local_init(void);
static int bmc156_local_remove(void);
static struct acc_init_info bmc156_init_info = {
 .name = "bmc156_acc", .init = bmc156_local_init, .uninit = bmc156_local_remove,
};

static int bmc156_probe(struct i2c_client *client, const struct i2c_device_id *id)
{
 struct bma255_i2c_data *obj;
 struct device_node *cust;
 struct acc_control_path ctl = {0};
 struct acc_data_path data = {0};
 int err;
 if (obj_i2c_data) return -EBUSY;
 if (client->adapter->nr != 2 || client->addr != 0x11) return -ENODEV;
 obj = devm_kzalloc(&client->dev, sizeof(*obj), GFP_KERNEL);
 if (!obj) return -ENOMEM;
 cust = of_find_compatible_node(NULL, NULL, "mediatek,bmc156_acc");
 if (!cust) return -ENODEV;
 err = get_accel_dts_func(cust, &obj->hw);
 of_node_put(cust);
 if (err) return err;
 if (obj->hw.direction != 4 || obj->hw.power_id != -1 ||
     obj->hw.i2c_num != 2 || obj->hw.i2c_addr[0] != 0x11 ||
     obj->hw.power_vol || obj->hw.firlen || obj->hw.is_batch_supported) return -EINVAL;
 err = hwmsen_get_convert(obj->hw.direction, &obj->cvt);
 if (err) return err;
 obj->client = client;
 obj->bandwidth = BMA255_BW_100HZ;
 mutex_init(&obj->lock);
 i2c_set_clientdata(client, obj);
 err = bmc156_init_client(obj);
 if (err) return err;
 obj_i2c_data = obj;
 data.get_data = bmc156_get_data;
 data.vender_div = 1000;
 err = acc_register_data_path(&data);
 if (err) goto fail;
 ctl.enable_nodata = bmc156_enable;
 ctl.batch = bmc156_batch;
 ctl.flush = bmc156_flush;
 ctl.set_cali = bmc156_set_cali;
 ctl.is_report_input_direct = false;
 ctl.is_support_batch = false;
 ctl.is_use_common_factory = false;
 err = acc_register_control_path(&ctl);
 if (err) goto fail;
 bma255_init_flag = 0;
 return 0;
fail:
 obj_i2c_data = NULL;
 return err;
}

static int bmc156_suspend(struct device *dev)
{
 struct bma255_i2c_data *obj = i2c_get_clientdata(to_i2c_client(dev));
 int err;
 acc_driver_pause_polling(1);
 mutex_lock(&operation_lock);
 err = BMA255_SetPowerMode(obj->client, false);
 if (!err) obj->suspended = true;
 mutex_unlock(&operation_lock);
 if (err) acc_driver_pause_polling(0);
 return err;
}
static int bmc156_resume(struct device *dev)
{
 struct bma255_i2c_data *obj = i2c_get_clientdata(to_i2c_client(dev));
 int err;
 mutex_lock(&operation_lock);
 err = bmc156_init_client(obj);
 if (!err) obj->suspended = false;
 mutex_unlock(&operation_lock);
 if (!err) acc_driver_pause_polling(0);
 return err;
}
static SIMPLE_DEV_PM_OPS(bmc156_pm, bmc156_suspend, bmc156_resume);
static const struct of_device_id bmc156_of_match[] = {
 {.compatible = "mediatek,gsensor"}, {},
};
static const struct i2c_device_id bmc156_ids[] = {{"bmc156_acc", 0}, {}};
static struct i2c_driver bmc156_driver = {
 .driver = {.name = "bmc156_acc", .of_match_table = bmc156_of_match, .pm = &bmc156_pm, .suppress_bind_attrs = true},
 .probe = bmc156_probe, .id_table = bmc156_ids,
};
static int bmc156_local_init(void)
{
 int err = i2c_add_driver(&bmc156_driver);
 if (err) return err;
 if (bma255_init_flag) { i2c_del_driver(&bmc156_driver); return bma255_init_flag; }
 return 0;
}
static int bmc156_local_remove(void)
{
 /* Built-in only: the core has no safe unregister-data-path operation. */
 return -EOPNOTSUPP;
}
static int __init bmc156_init(void)
{
 BUILD_BUG_ON(sizeof(struct sensor_event) != 36);
 BUILD_BUG_ON(offsetof(struct sensor_event, word) != 12);
 BUILD_BUG_ON(offsetof(struct sensor_event, flush_action) != 9);
 BUILD_BUG_ON(DATA_ACTION != 0 || FLUSH_ACTION != 1);
 return acc_driver_add(&bmc156_init_info);
}
module_init(bmc156_init);
MODULE_LICENSE("GPL v2");
MODULE_DESCRIPTION("ASUS P00A OEM BMC156 accelerometer, sensor_event ABI");
'''
result=head+rd+wr+res+raw+reg+body
(D/'bmc156_acc.c').write_text(result)
(D/'Makefile').write_text('ccflags-y += -I$(srctree)/drivers/misc/mediatek/sensors-1.0/accelerometer/inc\nccflags-y += -I$(srctree)/drivers/misc/mediatek/sensors-1.0/hwmon/include\nobj-y += bmc156_acc.o\n')
(D/'Kconfig').write_text('config BMC156_ACC\n\tbool "ASUS P00A OEM BMC156 accelerometer"\n\tdepends on CUSTOM_KERNEL_ACCELEROMETER && MTK_SENSORS_1_0 && !CUSTOM_KERNEL_SENSORHUB\n\tdefault n\n')
(S/'patches/oem-driver-adaptation.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),result.splitlines(True),fromfile='a/bmc156_acc.c',tofile='b/bmc156_acc.c')))
print('OEM-derived port',len(result.splitlines()),'lines')
