# Experiment52: release PCM on idle and safely resume browser audio

Actual tablet result: PASS. The existing guarded PulseAudio17 sink now loads only one additional standard module, module-suspend-on-idle timeout=5. It releases DL1 when idle rather than writing silence indefinitely. No amplifier route is enabled by this change, and no battery-life measurement is claimed.

The owned audio helper verifies either a suspended sink with kernel PCM closed, or an open native S16_LE/48000/stereo RW_INTERLEAVED PCM owned by a thread of its exact PulseAudio process. It retains exact executable/PID/start-time/boot/config guards and rejects data-buffer mappings. Kernel hw_params is checked whenever the PCM is open. Firefox's bare-hw ALSA fallback guard remains in place.

One actual idle/playback/idle experiment passed with the SAME PulseAudio daemon:

- Before playback: SUSPENDED, kernel PCM closed, no PCM fd in PulseAudio, both amps off.
- Real unmuted Firefox H264+AAC:9.624687seconds,232frames,4drops,errornull,volume0.05. Kernel native RW_INTERLEAVED parameters and owned PulseAudio stream verified; Firefox had no hardware PCM fd/map.
- After pause and dashboard navigation: SUSPENDED, PCM closed and no PCM fd, both amps off, daemon unchanged, no new kernel oops.

The current desktop used the installed helper after an ordinary desktop restart. This revision has not had an additional kernel reboot; the unchanged desktop startup integration was already proved through the experiment50 reboot. No new package, kernel/recovery/BCB/firmware/calibration changes, physical handling, USB operation or cloud resource. The owner is away; physical checks remain deferred.

Preimages are retained privately on SD at private/before-audio-idle/asus-goodix-audio and serial.pa. Removing only the added module line plus restoring the prior helper returns the already-proven continuously open serial sink. Do not remove the bare-hw fallback guard, change mmap=0, or run default.pa.

Source basis: PulseAudio17 module-suspend-on-idle.c schedules idle suspension and resumes on stream activity; alsa-sink.c unsuspend retains use_mmap/use_tsched and rejects changes to the original access mode or sample spec. Sources: https://raw.githubusercontent.com/pulseaudio/pulseaudio/v17.0/src/modules/module-suspend-on-idle.c and the existing pinned sources/alsa-mmap-opus/pulseaudio/src_modules_alsa_alsa-sink.c. Fetched idle-module source SHA2562201cb1a27eaf3df8394ad83c1fae2cbe08b31982259cdde0a7639966bcd4cfa, retained in the ignored source folder.

This module closes PCM only. It does NOT run UCM DisableSequence or turn off physical speaker amps. Automatic amplifier lifecycle remains separate; do not claim it is solved by idle suspension.
