set -eu
printf 'ALPINE '; cat /etc/alpine-release
printf 'BOOT '; cat /proc/sys/kernel/random/boot_id
df -h / /tmp /dev/shm
apk info | sort | sed -n '/alsa/p;/pulse/p;/ffmpeg/p;/firefox/p;/^libav/p;/^.*codec/p;/^pipewire/p'
printf '\nMEDIA PROCESSES\n'
ps -ef | sed -n '/[f]irefox/p;/[p]ulse/p;/[p]ipewire/p'
printf '\nAUDIO DEVICES\n'
cat /proc/asound/cards /proc/asound/pcm
ls -l /dev/snd
printf '\nAUDIO TOOLS\n'
for command in amixer aplay pactl pulseaudio ffmpeg ffprobe curl xdotool; do command -v "$command" || :; done
printf '\nCONFIG FILES\n'
for file in /etc/asound.conf /root/.asoundrc /etc/pulse/default.pa /etc/pulse/client.conf; do
 if [ -f "$file" ]; then printf '%s\n' "$file"; sed -n '1,130p' "$file"; fi
done
printf '\nFIREFOX LIBRARIES\n'
find /usr/lib -maxdepth 2 -name 'libavcodec*' -o -name 'libpulse.so*' -o -name 'libasound.so*'
