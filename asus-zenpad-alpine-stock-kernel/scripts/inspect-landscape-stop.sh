set -eu
printf 'GUI PROCESSES\n'
ps -ef | sed -n '/[X]org/p;/[a]sus-goodix-desktop/p;/[a]sus-jwm/p;/[o]nboard/p;/[d]bus-run-session/p'
printf '\nDISPLAY FILES\n'
ls -l /tmp/.X11-unix /tmp/.X0-lock /run/asus-goodix/desktop.pid 2>/dev/null || :
if [ -f /tmp/.X0-lock ]; then cat /tmp/.X0-lock; fi
printf '\nX SOCKET IN KERNEL\n'
sed -n '/X11-unix/p' /proc/net/unix
printf '\nDESKTOP LOG\n'
tail -45 /run/asus-goodix/desktop.log
printf '\nXORG LOG\n'
tail -35 /run/asus-goodix/Xorg.log
printf '\nTRIAL FILES\n'
ls -l /run/asus-goodix/rotation-trial
