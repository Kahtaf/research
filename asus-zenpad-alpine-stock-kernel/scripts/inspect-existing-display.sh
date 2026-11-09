id
ls -l /tmp/.X11-unix /usr/local/bin/asus-goodix-desktop /usr/local/bin/goodix-*.py 2>/dev/null
ps | grep -E 'Xorg|jwm|asus-goodix|firefox' | head -20
ls -la /run/asus-goodix /run/asus-alpine 2>/dev/null
cat /run/asus-alpine/sd-root-build.json
