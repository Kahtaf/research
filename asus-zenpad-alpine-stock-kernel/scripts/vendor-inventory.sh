ls -ld /vendor /system/vendor /etc/firmware /system/etc/firmware /vendor/firmware /system/vendor/firmware 2>/dev/null || true
ls -l /proc/265/exe /proc/265/root /proc/265/cwd
cat /proc/265/maps
ls -l /system/vendor/bin/wmt* /system/vendor/firmware/* /system/etc/firmware/* /etc/firmware/* 2>/dev/null || true
cat /proc/265/mountinfo
ls -l /data/nvram/APCFG/APRDEB/WIFI* /data/nvram/APCFG/APRDCL/* /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/misc 2>/dev/null || true
