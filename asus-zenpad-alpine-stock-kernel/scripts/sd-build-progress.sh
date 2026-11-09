cat /run/asus-alpine/sd-root-build.json
p=$(cat /run/asus-alpine/sd-root-build.pid)
if [ -r /proc/$p/status ]; then grep -E 'Name:|State:' /proc/$p/status; fi
