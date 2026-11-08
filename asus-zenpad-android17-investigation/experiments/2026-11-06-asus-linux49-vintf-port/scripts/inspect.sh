set -eu
cd /srv/android/lineage24
printf 'LIBVINTF\n'
rg -n 'first_api_level|Shipping FCM|target.level|infinitely old|UNSPECIFIED|kernel FCM' system/libvintf/{VintfObject.cpp,RuntimeInfo.cpp,KernelInfo.cpp,CompatibilityMatrix.cpp,assemble_vintf.cpp,check_vintf.cpp} | head -150
printf 'RETAINED KERNEL FILES\n'
find kernel/configs -maxdepth 3 -type f -name '*4.9*' -o -name 'android-base*' -o -name 'Android.bp' | head -100
printf 'MATRIX FILES\n'
ls hardware/interfaces/compatibility_matrices
printf 'DEVICE INPUTS\n'
cat device/asus/p00a/{BoardConfig.mk,manifest.xml,device.mk}
printf 'IMMUTABLE METADATA\n'
find out/target/product/p00a/system/etc/vintf out/target/product/p00a/system/vendor/etc/vintf -maxdepth 2 -type f -printf '%p %s\n'
printf 'KERNEL ARTIFACTS\n'
ls /srv/android/asus-bmc156-full-kernel-r1
