**Paused source archive:** The authored builder/harness/gates are included; the input directory, upstream sources, media and outputs are not. See ../../BUILD-INPUTS.md and ../../reports/private-ffmpeg61-result.md for prerequisites and actual tablet results.

# Public FFmpeg 61 build and validation staging

Question: can unpatched minimal FFmpeg7.1.5 satisfy Firefox ESR140's v61 ABI without ELF TLS or external dependencies?
Status: complete offline; all gates pass. See artifacts/browser-ffmpeg61/README.md and gates.json.
Input contains public upstream tarball, pinned Firefox wrapper source and retained synthetic media only. build.sh runs in the pinned, bounded disposable container, harness.c dlopens and decodes with the private closure, gates.py checks ELF/ABI/maps/counts. Continue through the parent-owned tablet trial; no deployment is performed here.
