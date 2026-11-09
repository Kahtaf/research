set -eu
apk add --no-cache xf86-video-dummy
apk info -v xf86-input-evdev xf86-video-dummy
