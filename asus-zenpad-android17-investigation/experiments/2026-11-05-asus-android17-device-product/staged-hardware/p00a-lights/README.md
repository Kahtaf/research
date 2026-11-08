# ASUS backlight service

Android 17 AIDL lights adapter for the existing MT8163 LED-class PWM backlight.
The 4.9 ASUS kernel bridge uses that same LED-class control to drive LP8557
enable/power sequencing. Stock read-only evidence confirms the class path,
canonical path and maximum brightness 255. This service does not write I2C
registers or introduce a second controller for the backlight.

Status: staged for compilation after the active framework build. Not installed
on the tablet; runtime brightness and screen-off/resume remain unverified.

The full product needs the service in PRODUCT_PACKAGES, its VINTF fragment and
the following device-policy entries before an enforcing hardware boot:

```
# file_contexts
/(vendor|system/vendor)/bin/hw/android\.hardware\.lights-service\.asus-p00a u:object_r:hal_light_default_exec:s0

# genfs_contexts (confirm canonical path on the 4.9 kernel)
genfscon sysfs /devices/platform/leds-mt65xx/leds/lcd-backlight u:object_r:sysfs_leds:s0

# hal_light_default.te
allow hal_light_default sysfs_leds:dir search;
allow hal_light_default sysfs_leds:file rw_file_perms;
```

Only the physical backlight is advertised. There is no invented notification LED
or battery LED. The stable V2 interface covers static backlight control.
