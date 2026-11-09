# Experiment51: muted YouTube sample on the actual tablet

After experiment50 fixed AAC decoding and the separate stock ALSA output crash, the unchanged owner Firefox played Google's documented IFrame API sample M7lc1UVf-VE on the tablet through its working Wi-Fi connection. No handling or owner input was required; the tablet stayed stationary because the owner is away and its USB port is mechanically unreliable.

The real player reported15.809640seconds, playback state1, qualitylarge, duration1344seconds, and no player/API/autoplay error. Every recorded playing-state sample was muted. A trusted software button activation initiated playback. At15seconds the fixture requested pause; the following player event confirmed state2. Cross-origin frame-drop statistics are unavailable through this API, so no frame-rate/drop claim is made.

The test ran after the unaccepted landscape trial automatically restored portrait800x1280. The owned serial PulseAudio service remained ready, hardware parameters were RW_INTERLEAVED, both amp gates were off and no new kernel oops was observed. This is one real streamed YouTube sample, not physical audibility or qualification of all videos/DRM/high resolutions. Browser speaker audibility and safe automatic amp lifecycle still need work; physical landscape/typing checks remain deferred until the owner returns.

The browser was returned to the local dashboard, and the five-minute loopback observer was explicitly stopped. No new network service or cloud resource was created. User profile/history were retained. Public receipt: evidence/youtube-muted-workload.json. Raw player state and cleanup result are ignored under private/live/youtube-owner-away-result.txt.
