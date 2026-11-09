set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
cat /run/asus-goodix/rotation-trial/state.json
xdotool getdisplaygeometry
xprop -root _NET_ACTIVE_WINDOW _NET_SUPPORTING_WM_CHECK _NET_CLIENT_LIST
ps -ef | sed -n '/[a]sus-jwm/p;/[f]irefox.*--profile/p;/[X]org/p'
printf '\nJWM\n'; cat /run/asus-goodix/jwm.log
printf '\nDESKTOP\n'; tail -20 /run/asus-goodix/desktop.log
xwd -root -silent -out /tmp/asus-landscape-trial/root.xwd
