set -eu
python3 - <<'PY'
from pathlib import Path
import json, os, shutil, subprocess
assert Path('/run/asus-alpine/root-mode').read_text().strip() == 'SD-loop'
assert not Path('/etc/asus-alpine/enable-gui').exists()
assert not Path('/tmp/.X11-unix/X0').exists()
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip() == 'closed'
for name in ('Ext_Speaker_Amp_Switch', 'Speaker_Amp_Switch'):
    assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name], text=True)
guard = Path('/etc/asound.conf')
assert not guard.exists() and not guard.is_symlink(), 'Inspect an existing ALSA configuration'
backup = Path('/mnt/alpine-sd/2026-11-08-asus-alpine/private/before-rw-pulse')
assert not backup.exists()
backup.mkdir(mode=0o700)
shutil.copy2('/etc/apk/world', backup/'apk-world')
prefs = Path('/etc/asus-goodix/firefox-user.js')
shutil.copy2(prefs, backup/'firefox-user.js')
(backup/'preimage.json').write_text(json.dumps({'asound_conf_existed':False,'gui_held':True})+'\n')
# A bare hw default makes Firefox's FLOAT_LE ALSA fallback fail before mapping.
guard.write_text('# asus-alsa-rw-guard-v1\npcm.!default { type hw card 0 device 0 }\nctl.!default { type hw card 0 }\n')
guard.chmod(0o644)
text = prefs.read_text()
assert 'browser.sessionstore.resume_from_crash' not in text
assert 'media.autoplay.default' not in text
prefs.write_text(text+'\n// Keep an unclean media session from restarting without an explicit play.\nuser_pref("browser.sessionstore.resume_from_crash", false);\nuser_pref("media.autoplay.default", 5);\n')
os.sync()
print('ALSA_FALLBACK_GUARD_AND_CRASH_STARTUP_PREFS_INSTALLED', flush=True)
PY
apk add --no-cache --virtual .asus-pulse-rw-trial pulseaudio=17.0-r7 pulseaudio-alsa=17.0-r7 libpulse=17.0-r7 pulseaudio-utils=17.0-r7
apk info -v pulseaudio pulseaudio-alsa libpulse pulseaudio-utils
