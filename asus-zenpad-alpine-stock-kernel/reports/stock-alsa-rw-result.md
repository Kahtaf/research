# Experiment50: stock ALSA output repaired in userspace

The retained crash is explained by the original DL1 `.page` callback returning a bogus `struct page` for an mmapped PCM buffer. Firefox requested float samples; ALSA's implicit converter selected the falsely advertised hardware MMAP path. Source review: opus-alsa-mmap-oops.md. The stock kernel is unchanged.

## Actual recovery and playback

Exact stock Android identity and Enforcing were revalidated. Original BOOT and canonical stock recovery were fully hashed, geometry checked, and all2048 BCB bytes matched the existing command-only Linux selection. Only the SD GUI marker was renamed to GUI.ENABLE.held-for-audio before reapplying the already-proven recovery capsule. Full recovery/BOOT read-back and byte-for-byte unchanged BCB passed. No BOOT, SYSTEM, GPT, bootloader or factory write. The current SD OS image was neither mounted nor modified from Android.

An ordinary reboot reached Alpine3.24.4 on stock3.18.35 and authenticated with the previous pinned SSH host key. GUI was held; dashboard had49 saved requests, private decoder hashes survived, closed browser history quick_check was ok, and PCM/amps were off. Root was rebound only after new-boot, kernel, root-mode and exact BCB guards passed.

Installed Alpine17.0-r7 pulseaudio, pulseaudio-alsa, libpulse and pulseaudio-utils using virtual .asus-pulse-rw-trial. APK also selected its normal dependencies, including pulseaudio-openrc; this BusyBox init does not run an OpenRC service. Default PA scripts were never executed. No alsa-plugins-pulse was installed. A private preimage of APK world and Firefox user.js is in the SD private/before-rw-pulse folder.

The ALSA fallback guard `/etc/asound.conf` makes default a bare hw PCM. Firefox's float fallback is refused before converter/MMAP setup. Persistent startup prefs disable crash session resume and block autoplay pending an explicit play. They do not alter Firefox sandboxing. Their source is `/etc/asus-goodix/firefox-user.js`; launcher copies it into the existing profile. Pref values persist in prefs.js, so rollback must reset values once, not merely delete user.js lines. Owner profile/session files were not deleted.

PulseAudio ran under strace with an exact script loading only module-alsa-sink hw:0,0 mmap=0 tsched=0 s16le/48000/2 and native Unix protocol. Kernel hw_params actually showed RW_INTERLEAVED/S16_LE/48000/2. The only PCM mmap attempts were status/control offsets0x80000000 and0x81000000 (both returned ENXIO, so ALSA used its ioctl fallback). No data offset0 mapping occurred. Sink access_mode was serial, no plug fallback, both amp switches off.

One unmuted local H264+AAC workload then played9.75452seconds,235frames,4drops, no media error, volume0.05, speaker amps off. PulseAudio created a float32le mono48k AudioStream for Firefox and converted it to native stereoS16. Firefox parent mapped libpulse; all10 Firefox processes were checked for no hardware PCM fd/map. Utility remained Seccomp2. No new kernel oops. This is decoding AND output qualification; physical browser audibility remains untested.

The first pactl observation ran immediately before stream creation and captured an empty list. The completed playback was not repeated: subsequent pactl and the daemon's native stream-creation log confirmed the same still-existing Firefox stream. The observer source now retries until a Firefox stream is present. Public result: evidence/stock-alsa-rw-browser-result.json. Raw log/trace archive is ignored private/live/rw-pulse-evidence-before-reboot.tar.gz.

## Startup integration

`overlay/goodix/bin/asus-goodix-audio` is installed as a separate owned service with start/stop/status, exact PID/start-time/boot/executable/command checks, locked RAM state and a fixed safe module script. It never loads default.pa or writes a mixer. It verifies kernel format/access, absence of hardware data mapping and serial sink before readiness. Existing/unowned daemons and unexpected ALSA config are refused.

The desktop starts it before Firefox when `/etc/asus-goodix/audio=pulse-rw-v1`. Cleanup terminates only its owned daemon after stopping desktop clients, verifies PCM closed and amps off, and removes its own PID record. Original desktop helper is backed up privately on SD. GUI.ENABLE was restored only after the new service and native portrait desktop were actually live. A complete desktop stop then passed browser history integrity18entries and PCM-closed service shutdown.

Ordinary kernel reboot verification PASSED: the same pinned host key authenticated a new SD-root boot with exact BCB. Owned PulseAudio auto-started before Firefox with RW hardware parameters; portrait800x1280, native16-contact touch, Onboard, FirefoxXI2 and dashboard58saved requests all passed. Amp gates remained off; no new kernel oops. No suspend/cold-power qualification, idle suspend integration or persistent amplifier route is claimed. The current sink writes silence continuously while the desktop runs; idle power work remains.

## Implementation corrections and rollback

The consultation's default-sample-rate and alternate-sample-rate command-line flags are unsupported in this PA build; first launch refused them before opening PCM. They were removed; exact sink format/rate/channels are already fixed in the module script. This kernel lacks /proc/PID/task/PID/children; parent discovery used PPid instead. Early Android preflight refusals were stock stat/alias assumptions and occurred before SD-marker or partition writes. All raw attempts are retained privately.

For rollback, first close the owned desktop normally, which stops the owned PA daemon and leaves amps off/PCM closed. Keep the bare-hw ALSA guard: removing it while Firefox can fall back to ALSA restores the known kernel crash. Disable only the audio marker to keep silent fail-closed Firefox if needed. Original helper and package-world/prefs preimages are privately retained; do not remove the guard simply to recover sound. To revert the two startup prefs, restore the preimage and explicitly reset browser.sessionstore.resume_from_crash=true and media.autoplay.default=1 once while Firefox is closed. No broad media.allow-audio-non-utility preference or utility-disable policy was enabled.

Fresh landscape follow-up: after the reboot pass, a RAM-only CW session was started with watchdog961. Browser title ASUS landscape trial and root1280x800/native16 were verified; CSSscreen1024x640 matches1.25scaling. The six-minute physical timer is now live on the boot pinned in private/standalone-ssh.json. No persistent rotation marker. Check the live watchdog before accepting; never reuse this note as fresh timer evidence.

Owner-away follow-up: the owner reports a finicky tablet USB port, so physically rotating it can disconnect USB. The landscape trial was left unaccepted and timed out; watchdog961 restored portrait and independent Xorg geometry check showed800x1280. No physical touch evidence was produced. The first observer queried X before it was ready; the subsequent actual display check passed. Physical rotation/audibility checks are deferred, with Wi-Fi SSH primary.
