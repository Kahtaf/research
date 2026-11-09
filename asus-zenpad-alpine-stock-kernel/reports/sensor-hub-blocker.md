# Stock accelerometer branch parked

Opus offline binary review found that the actual stock kernel (Aug9,2018, firmware5.3.20) differs from the retained V4.7.0 source (Jan2017). The running binary omits android_gsensor and includes a delayed sw_cali loader absent in that source. It also contains the SENSORHUB branch. Treat the retained tree as an older reference, not exact source for callback safety.

The hub data path requires MD32, while Alpine startup has no operation that boots it. A passive check of the existing kernel log and /proc/interrupts found0relevant retained log lines and MD32 IRQ counts0/0/0. This is consistent with an inactive hub; absence of logs and interrupts is not direct proof of reset state, especially with a wrapped log ring. md32_boot was neither read nor written. No sensor or calibration operation occurred.

This does NOT establish a safe activation baseline. In the older source model, enabling without MD32 changes cached demand/power flags but cannot produce samples or restore reliably. Booting MD32 starts a persistent co-processor lifecycle and can issue a calibration-reset action. With unmatched source and opaque hub state, neither action is qualified. Active accelerometer work is stopped within the present scope. The working OS, Wi-Fi, SSH and portrait desktop are not blocked by this.

ASUS official Z380M source catalog was checked: newest listed kernel source V4_7_0,Jan5,2017,682.99MB; older V4_2_0 andV4_1_1 are also listed. No matching5.3.20/2018 source is listed there. Primary source: https://www.asus.com/supportonly/asus%20zenpad%208.0%20(z380m)/helpdesk_download/. No large downloads, guessed URLs, alternate-device sources or new resources were used.

Smallest next requirement: obtain source matching the installed2018firmware, then separately qualify a calibration-preserving MD32/hub lifecycle. Do not boot MD32, write accactive/accenablenodata/accdelay/accbatch/cpsopmode, or invoke gsensor ioctls. Don't read calibration or apparent-read sensor data callbacks. Automatic orientation stays parked; native portrait stays selected. Existing bounded manual landscape remains a separate display/touch trial needing later physical confirmation.

The prior three-second passive input observation produced0frames. Its cpsopmode/accdevnum reads relied on older-source callback assumptions. Their observations are retained as historical evidence, not a basis for further driver reads. The passive observer source has now been reduced to input-core name/dev metadata, cached EVIOCGABS and nonblocking evdev reads only; it no longer accesses sensor-driver attributes. That deletion was syntax-checked without repeating the device experiment.

Evidence: md32-passive-result.json and asus-source-catalog.json under evidence/. Raw logs stay ignored in private/live. Full binary/source consultation: opus-accelerometer-baseline.md. Live sensor-hub work remains parked; independent usability work continues.
