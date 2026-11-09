# Offline stock-speaker UCM2 candidate

**Parent experiment48 update:** the candidate passed the actual tablet's read-only parser/discovery gate. First parse found that master Syntax2 cannot substitute CardNumber; alsa-lib's `rval_card_number()` explicitly returnsNULL below syntax3. Master was corrected to Syntax4, preserving the same route. Actual alsa-lib1.2.15.3-r0 / alsaucm1.2.15.2 then listed exactly HiFi/Speaker and returned PCMhw:0,0,48000,2. Both amp gates stayed0, class stayed0 and gain stayed1. No verb/device was selected and no global configuration/service was installed. Raw observations are private/live/ucm-parser-first.txt and ucm-parser-corrected.txt; sanitized result is evidence/speaker-ucm-parser.json. The idle lifecycle limitation below remains unresolved. The original offline review follows.

2026-11-08. No tablet, SSH, ADB, UI, installation, package, server or build
operation. This is a small reviewable configuration, not a deployed audio path.

## Files and exact scope

- `overlay/goodix/ucm2/ASUS/Z380M/Z380M.conf`: one HiFi use case.
- `overlay/goodix/ucm2/ASUS/Z380M/HiFi.conf`: one Speaker device.
- `overlay/goodix/ucm2/conf.d/mt-snd-card/mt-snd-card.conf`: relative symlink to
  that master file.
- `overlay/goodix/ucm2/ucm.conf`: minimal isolated lookup root for candidate tests.

Observed card0 driver/longname are `mt-snd-card`; its ALSA card ID is
`mtsndcard`. Upstream discovery uses driver and longname, not card ID. The
conf.d link covers the former and the sequences/PCM use `${CardNumber}` so
control and playback target the same discovered card. Physical discovery with
the installed target alsa-lib is still a gate, not an offline finding.
Do not install this minimal root over the distribution's `ucm.conf`; eventual
integration adds only ASUS/Z380M and its conf.d link to the normal tree.

Speaker EnableSequence fixes `Audio_Speaker_PGA_gain=0Db`, selects CLASSAB,
enables Speaker_Amp_Switch, then Ext_Speaker_Amp_Switch, and waits25ms.
Both device DisableSequence and verb DisableSequence disable Ext first,
then Speaker. This duplicates the off operation on a full verb transition
intentionally; writes are idempotent. HiFi selection alone does not power up.
No BootSequence/FixedBootSequence/Defaults operation is present, so opening and
listing this candidate has no mixer sequence to execute.

The XML/stock route and running GPIO28/CONFIG_MTK_SPEAKER evidence belong to
the existing audit and direct-tone qualification. This candidate adds no GPIO,
clock, interconnect, headphone, capture, trim or calibration writes. The gain
label `Mute` is never used: the driver clamps it to0Db. The fixed gain/class
are not automatically restored to a prior owner's settings; the future trial
must save them and restore after both amps are off. Admit only an idle,
initially unpowered route. UCM itself does not arbitrate concurrent clients or
provide transactional rollback if a sequence fails partway through.

PlaybackPCM is `hw:${CardNumber},0`, PlaybackRate48000 and PlaybackChannels2.
The future PulseAudio module must request S16_LE as below; UCM rate/channel
metadata alone does not enforce format for arbitrary ALSA clients. No
PlaybackVolume, PlaybackSwitch, PlaybackMixerElem or master element maps the
misleading controls. PulseAudio software volume is intended. A raw `aplay`
invocation does not automatically consume UCM route sequences.

## Source basis and limits

Checked primary upstream source on2026-11-08:

- [alsa-ucm-conf lookup root](https://github.com/alsa-project/alsa-ucm-conf/blob/master/ucm2/ucm.conf)
  defines conf.d driver/longname lookup; [its README](https://github.com/alsa-project/alsa-ucm-conf/blob/master/ucm2/README.md)
  distinguishes driver from card name.
- [alsa-lib parser](https://github.com/alsa-project/alsa-lib/blob/master/src/ucm/parser.c)
  documents/parses cdev, cset and integer-microsecond usleep in ordered
  sequences, honors ALSA_CONFIG_UCM2 and parses use-case/device sections.
  [use-case.h](https://github.com/alsa-project/alsa-lib/blob/master/include/use-case.h)
  defines PlaybackPCM/CTL, PlaybackRate, PlaybackChannels and lookup identifiers.
- [alsa-utils alsaucm](https://github.com/alsa-project/alsa-utils/blob/master/alsaucm/usecase.c)
  sends `list`/`get` to the UCM list/get APIs. No `_verb` or `_enadev` set is
  necessary for the explicit-verb lookup below.
- [PulseAudio module-alsa-card](https://github.com/pulseaudio/pulseaudio/blob/v17.0/src/modules/alsa/module-alsa-card.c)
  accepts device_id, use_ucm, profile, rate, format, tsched and mmap.
  [alsa-ucm.c](https://github.com/pulseaudio/pulseaudio/blob/v17.0/src/modules/alsa/alsa-ucm.c)
  consumes UCM PCM/rate/channel/volume properties and executes device transitions.

No host alsaucm is available, and no package/build was authorized for this
subtask. That offline review did not claim a parser pass. The parent subsequently
passed the following read-only target gate; activation remains untested.

## Exact next gate: read-only target parser/list

After the parent safely stages this complete candidate tree at a private
absolute RAM/SD path (bind CANDIDATE_UCM2 to that real path), use the already
available alsaucm binary with the same environment for each invocation:

```sh
env ALSA_CONFIG_UCM2="$CANDIDATE_UCM2" alsaucm -c hw:0 list _verbs
env ALSA_CONFIG_UCM2="$CANDIDATE_UCM2" alsaucm -c hw:0 list _devices/HiFi
env ALSA_CONFIG_UCM2="$CANDIDATE_UCM2" alsaucm -c hw:0 get '=PlaybackPCM/Speaker/HiFi'
env ALSA_CONFIG_UCM2="$CANDIDATE_UCM2" alsaucm -c hw:0 get '=PlaybackRate/Speaker/HiFi'
env ALSA_CONFIG_UCM2="$CANDIDATE_UCM2" alsaucm -c hw:0 get '=PlaybackChannels/Speaker/HiFi'
```

Require exactly HiFi and Speaker, `hw:0,0`,48000,2, no parser/substitution error,
and unchanged amp-off/PCM-idle state before/after. Save bounded output privately.
Do not set a verb/device, call reset/defaults, or infer playback from listing.
Failure means inspect discovery/parser evidence; no fallback generic profiles.

## Future bounded ordinary-playback gate

Only after that gate, review the installed PulseAudio version/build, module
availability and linked UCM support. Manual `module-alsa-card` loading avoids
requiring module-udev-detect or a running udev daemon for discovery. It does not
prove this build will operate without udev metadata: source/build, permissions,
card access, session runtime and module behavior must be checked. Do not add
udev or alter the working input metadata to make audio discovery work.

A future private test server's environment must contain ALSA_CONFIG_UCM2 before
startup (pactl's environment cannot change an existing server). The minimal
card-module argument shape supported by upstream17.0 is:

```text
load-module module-alsa-card device_id=0 use_ucm=yes profile=off rate=48000 format=s16le tsched=0 mmap=0
```

This is a reviewed argument candidate, not a startup file or instruction to
start a server now. `profile=off` avoids initial route activation; explicit
use_ucm=yes must be verified in logs because a failed UCM probe can lead to
fallback. Require the enumerated card to offer only the expected UCM output
plus off, no phantom input/headphone profiles, before selecting its actual
reported HiFi profile. Configure software volume, no amplification, no
restored client streams/default routing, and no other PCM owner. Snapshot the
four affected controls while the route is off; retain an independent bounded
cleanup guardian that disables Ext then Speaker and restores class/gain only
after off. This guardian is an experiment safeguard, not product integration.

Use one already-qualified one-second faded -40dBFS peak,48k S16_LE stereo WAV
through ordinary paplay, not mixer commands in the playback path. Bound the
whole active interval to10seconds. Record actual hw_params and owner audibility.
After the stream, select card off, unload the exact test card module and stop
the private server. Require Ext=Off, Speaker=Off, PCM closed, saved class/gain
restored and no new bounded kernel error. Any fault ends the gate; no gain
escalation, alternate GPIO or browser/decoder variant is implied.

## Automatic idle lifecycle remains a blocker

UCM describes explicit route transitions, not every PCM close. PulseAudio17's
alsa-sink suspend closes PCM, while its UCM device disable path is attached to
route/profile transitions. `module-suspend-on-idle` therefore must NOT be
claimed to execute these DisableSequences or power down either amplifier.
A complete future standard-component solution needs source-backed behavior
and a measured stream→idle→off transition, plus cleanup on ordinary server
exit. Profile off/unload supplies only the explicit bounded trial close gate.
No automatic lifecycle, persistent enabled route or active server is supplied
by this candidate. The decoder fix remains a separate task.
