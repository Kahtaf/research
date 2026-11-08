from pathlib import Path
S=Path(__file__).resolve().parents[1]; P=S/'source/kernel-preimages'; D=S/'source/kernel'
base='drivers/misc/mediatek/sensors-1.0/accelerometer/'
def write(n,s):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
s=(P/(base+'accel.c')).read_text()
s=s.replace('static struct acc_init_info *gsensor_init_list', 'static DEFINE_MUTEX(acc_sample_mutex);\n\nstatic struct acc_init_info *gsensor_init_list')
def replace_func(s,name,new):
 start=s.index('static '+name);end=s.index('\n}',start)+2
 return s[:start]+new+s[end:]
s=replace_func(s,'void acc_work_func', '''static void acc_work_func(struct work_struct *work)
{
 struct acc_context *cxt = acc_context_obj;
 int x, y, z, status, err;
 if (!cxt->acc_data.get_data) return;
 mutex_lock(&acc_sample_mutex);
 err = cxt->acc_data.get_data(&x, &y, &z, &status);
 if (!err) {
  cxt->drv_data.x = x; cxt->drv_data.y = y; cxt->drv_data.z = z;
  cxt->drv_data.status = status;
  cxt->drv_data.timestamp = getCurNS();
  /* No synthesized backfill, zero-vector suppression or -1 sentinel filtering. */
  err = acc_data_report(&cxt->drv_data);
 }
 if (err) pr_err_ratelimited("accelerometer read/report failed: %d\\n", err);
 mutex_unlock(&acc_sample_mutex);
 if (cxt->is_polling_run)
  startTimer(&cxt->hrTimer, atomic_read(&cxt->delay), false);
}''')
s=replace_func(s,'ssize_t acc_store_batch', '''static ssize_t acc_store_batch(struct device *dev,
 struct device_attribute *attr, const char *buf, size_t count)
{
 struct acc_context *cxt = acc_context_obj;
 int handle, flag, err;
 long long delay, latency, old_delay, old_latency;
 char tail;
 if (sscanf(buf, "%d,%d,%lld,%lld %c", &handle, &flag, &delay, &latency, &tail) != 4 ||
     handle != 0 || flag != 0 || latency != 0 || delay < 10000000 || delay > 200000000)
  return -EINVAL;
 mutex_lock(&cxt->acc_op_mutex);
 old_delay = cxt->delay_ns; old_latency = cxt->latency_ns;
 cxt->delay_ns = delay; cxt->latency_ns = latency;
 err = acc_enable_and_batch();
 if (err) { cxt->delay_ns = old_delay; cxt->latency_ns = old_latency; }
 mutex_unlock(&cxt->acc_op_mutex);
 return err ? err : count;
}''')
s=replace_func(s,'ssize_t acc_store_flush', '''static ssize_t acc_store_flush(struct device *dev,
 struct device_attribute *attr, const char *buf, size_t count)
{
 struct acc_context *cxt = acc_context_obj;
 int handle, err;
 if (kstrtoint(buf, 10, &handle) || handle != 0) return -EINVAL;
 mutex_lock(&cxt->acc_op_mutex);
 if (!cxt->is_active_data) err = -EINVAL;
 else if (!cxt->acc_ctl.flush) err = -EOPNOTSUPP;
 else {
  /* Serialize marker with the complete sample-read/report transaction. */
  mutex_lock(&acc_sample_mutex);
  err = cxt->acc_ctl.flush();
  mutex_unlock(&acc_sample_mutex);
 }
 mutex_unlock(&cxt->acc_op_mutex);
 return err ? err : count;
}''')
s=replace_func(s,'ssize_t acc_store_cali', '''static ssize_t acc_store_cali(struct device *dev,
 struct device_attribute *attr, const char *buf, size_t count)
{
 struct acc_context *cxt = acc_context_obj;
 int err;
 if (count != 12) return -EINVAL;
 mutex_lock(&cxt->acc_op_mutex);
 err = cxt->acc_ctl.set_cali ? cxt->acc_ctl.set_cali((uint8_t *)buf, count) : -EOPNOTSUPP;
 mutex_unlock(&cxt->acc_op_mutex);
 return err ? err : count;
}''')
# Strict boolean parsing and restore requested state if enable write fails.
s=s.replace('int err = 0;\n\n\tpr_debug("acc_store_active', 'int err = 0;\n\tint old_enable;\n\tbool old_active;\n\n\tpr_debug("acc_store_active',1)
s=s.replace('if (!strncmp(buf, "1", 1)) {','old_enable = cxt->enable; old_active = cxt->is_active_data;\n\tif (sysfs_streq(buf, "1")) {',1)
s=s.replace('} else if (!strncmp(buf, "0", 1)) {','} else if (sysfs_streq(buf, "0")) {',1)
# First occurrence of these strings in store_nodata differs; ensure scoped below.
start=s.index('static ssize_t acc_store_active');end=s.index('\n}',start)+2
part=s[start:end]
# If generic replacement above hit an earlier function, apply exact scoped repairs instead.
if 'old_enable = ' not in part:
 part=part.replace('if (!strncmp(buf, "1", 1)) {','old_enable = cxt->enable; old_active = cxt->is_active_data;\n\tif (sysfs_streq(buf, "1")) {').replace('} else if (!strncmp(buf, "0", 1)) {','} else if (sysfs_streq(buf, "0")) {')
part=part.replace('err_out:\n','err_out:\n\tif (err) { cxt->enable = old_enable; cxt->is_active_data = old_active; }\n')
s=s[:start]+part+s[end:]
# Repair any accidental change to nodata; no use of that interface by the new HAL.
start=s.index('static ssize_t acc_store_enable_nodata') if 'static ssize_t acc_store_enable_nodata' in s else -1
if start!=-1:
 end=s.index('\n}',start)+2
 orig=(P/(base+'accel.c')).read_text();os=orig.index('static ssize_t acc_store_enable_nodata');oe=orig.index('\n}',os)+2
 s=s[:start]+orig[os:oe]+s[end:]
start=s.index('static int acc_enable_and_batch');end=s.index('\n}',start)+2
part=s[start:end].replace('return -1;', 'return err;')
part=part.replace('return err;\n\t}', 'return -EBUSY;\n\t}',1)
s=s[:start]+part+s[end:]
start=s.index('static ssize_t acc_store_active');end=s.index('\n}',start)+2
s=s[:start]+s[start:end].replace('err = -1;', 'err = -EINVAL;')+s[end:]
write(base+'accel.c',s)
write(base+'Makefile',(P/(base+'Makefile')).read_text()+'\nobj-$(CONFIG_BMC156_ACC) += bmc156_acc/\n')
write(base+'Kconfig',(P/(base+'Kconfig')).read_text()+'\nsource "'+base+'bmc156_acc/Kconfig"\n')
p='arch/arm64/configs/asus_p00a_defconfig';s=(P/p).read_text().replace('CONFIG_MTK_BMA253=y','# CONFIG_MTK_BMA253 is not set').replace('# CONFIG_CUSTOM_KERNEL_ACCELEROMETER is not set','CONFIG_CUSTOM_KERNEL_ACCELEROMETER=y\nCONFIG_BMC156_ACC=y');s += '\n# CONFIG_MTK_MC3416 is not set\n';write(p,s)
p='drivers/misc/mediatek/sensors-1.0/hwmon/sensor_attributes/sensor_attr.c'
s=(P/p).read_text()
start=s.index('int sensor_attr_register(');end=s.index('\n}',start)+2
s=s[:start]+'''int sensor_attr_register(struct sensor_attr_t *misc)
{
 dev_t dev;
 int err = 0;
 struct sensor_attr_t *c;
 mutex_lock(&sensor_attr_mtx);
 list_for_each_entry(c, &sensor_attr_list, list) {
  if (c->minor == misc->minor) { err = -EBUSY; goto out; }
 }
 /* Queue must exist before publishing the device to userspace. */
 err = sensor_event_register(misc->minor);
 if (err) goto out;
 dev = MKDEV(sensor_attr_major, misc->minor);
 misc->this_device = device_create(sensor_attr_class, misc->parent, dev,
                                  misc, "%s", misc->name);
 if (IS_ERR(misc->this_device)) {
  err = PTR_ERR(misc->this_device);
  misc->this_device = NULL;
  sensor_event_deregister(misc->minor);
  goto out;
 }
 list_add(&misc->list, &sensor_attr_list);
out:
 mutex_unlock(&sensor_attr_mtx);
 return err;
}'''+s[end:]
write(p,s)
p=base+'accel.c';s=(D/p).read_text()
s=s.replace('pr_err("unable to create acc attribute file\\n");\n\t\treturn -3;', 'pr_err("unable to create acc attribute file\\n");\n\t\tsensor_attr_deregister(&acc_context_obj->mdev);\n\t\treturn err;')
s=s.replace('real_driver_init_fail:\n\tkfree(acc_context_obj);','real_driver_init_fail:\n\tdestroy_workqueue(acc_context_obj->accel_workqueue);\n\tkfree(acc_context_obj);\n\tacc_context_obj = NULL;')
assert 'if (!obj->accel_workqueue)' in s
write(p,s)

p=base+'accel.c';s=(D/p).read_text()
s=s.replace('\t\tcxt->is_acc_need_restore_polling = !!cxt->enable;\n','')
s=s.replace('already in pause, just save enable state: %d', 'paused: reject requested enable state: %d')
write(p,s)
p=base+'accel.c';s=(D/p).read_text()
s=s.replace('if (cxt->power == 1 && cxt->enable == 0) {','if (cxt->enable == 0) {')
s=s.replace('\t\tcxt->delay_ns = -1;\n','')
write(p,s)
