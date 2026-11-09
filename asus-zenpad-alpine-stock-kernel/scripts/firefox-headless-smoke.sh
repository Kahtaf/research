set -eu
mkdir -p /tmp/firefox-smoke
XDG_RUNTIME_DIR=/run/user/0 timeout -k 2 40 firefox-esr --headless --no-remote --profile /tmp/firefox-smoke --screenshot /tmp/firefox-https.png --window-size 800,1280 https://alpinelinux.org/
ls -l /tmp/firefox-https.png
