# Z380M speaker UCM2 candidate

Question: can standard ALSA UCM represent the physically qualified stock speaker
route without a custom PCM plugin or route daemon?

Status: RAM PARSER PASS. The parent staged this candidate in RAM and the tablet's
actual alsa-lib/alsaucm passed discovery, HiFi/Speaker listing and PCM/rate/channel
queries. No verb/device was selected and all four mixer values were unchanged.
It is not globally installed, activated or connected to an audio server.

`Z380M.conf` exposes only `HiFi`; `HiFi.conf` exposes only `Speaker` at PCM0,
48 kHz stereo. Amp startup is Speaker then Ext; shutdown is Ext then Speaker.
Gain is fixed to enum `0Db` (index1); software should control playback volume.
There are no hardware volume/mute mappings, other routes, GPIO/calibration
operations, boot sequences, PCM hooks, or external commands.

The containing `ucm2/conf.d/mt-snd-card/mt-snd-card.conf` symlink is the normal
ALSA discovery entry for the observed driver and long name `mt-snd-card`.
Card ID `mtsndcard` is not the discovery directory. The containing `ucm.conf`
is an isolated candidate lookup root for `ALSA_CONFIG_UCM2`; it is not a
replacement for the distribution's complete installed lookup configuration.

Continue with [the report](../../../../../reports/speaker-ucm-candidate.md),
starting with the recorded parser result. Ordinary playback through UCM remains
unqualified. PulseAudio idle suspend alone does not execute
this route's DisableSequence; explicit off/unload is required for the bounded
future trial. Automatic idle amp power-down remains unresolved.
