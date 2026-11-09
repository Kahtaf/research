set -eu
[ ! -e /etc/apk/world.asus-before-audio ]
cp -p /etc/apk/world /etc/apk/world.asus-before-audio
apk add --no-cache --virtual .asus-audio-tools alsa-utils
amixer -c 0 controls > /tmp/asus-audio-controls.txt
amixer -c 0 contents > /tmp/asus-audio-contents.txt
cat /tmp/asus-audio-contents.txt
