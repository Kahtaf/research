# Stock ASUS audio topology

Question: what public ALSA card/PCM and driver metadata does normal stock Android expose?

Status: read-only parent capture attempted with exact stock fingerprint guard. No mixer control write, PCM open, playback, recording, GPIO operation, root helper or private calibration access.

Output: evidence/stock-topology.json records each command and actual result.

Continuation: compare public names/directions with staged HAL and kernel source. This inventory cannot determine the fitted amplifier, live control sequence, microphone wiring or acoustic behavior. Capture permissions may require a separately reviewed metadata-only reader; do not infer route readiness from successful enumeration.
