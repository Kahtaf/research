set -eu
tail -25 /run/asus-goodix/bridge.log
curl -fsS --max-time 3 http://127.0.0.1:8080/health
printf '\n'
