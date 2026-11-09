uname -rm
cat /proc/1/comm
ps
ls -l /dev/__properties__ /dev/stpwmt /dev/wmtWifi
sha256sum /dev/__properties__
p=$(cat /run/asus-alpine/wmt-launcher.pid)
echo LAUNCHER_PID=$p
readlink /proc/$p/exe
cat /proc/$p/wchan /proc/$p/syscall
ls -l /proc/$p/fd
grep -E 'State:|Uid:|Gid:' /proc/$p/status
cat /run/asus-alpine/wmt-launcher.log
cat /run/asus-alpine/sysinit.log
ip link show
dmesg | grep -Ei 'wmt|stp|wlan|firmware|consys|wifi' | tail -100
