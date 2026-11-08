# Usability is a separate acceptance result

The tablet's recorded stock `MemTotal` is2,000,192KiB, approximately1.91GiB
available to the kernel. This is an old stock observation, not an Android17
memory measurement. `MemAvailable` from that capture must not be reused as the
future product's headroom.

Prepared product source sets `ro.config.low_ram=true`, uses the2GiB tablet heap
profile, and configures bounded lz4 zRAM. The compiled physical kernel has PSI,
swap and zRAM enabled; MEMCG is disabled. Those are implementation inputs,
not proof that lmkd starts, pressure handling works, or the framework plus Google
services leaves enough usable memory. Do not blindly inherit a Go profile that
requires unsupported kernel features. A low-RAM flag does not produce a certified
Android17 Go product or change the physical CPU/GPU/storage limits.

The practical target is responsive light single-app use. Smooth modern
multitasking, heavy websites and games are not promised. Keep the Android17
objective and requested Google/root components; measure before changing scope.

## Evidence needed

1. Targeted isolated runtime: the genuine SDK37 lmkd ELF and matching kernel
   memory/PSI configuration actually start and handle pressure. Distinguish
   daemon-directed eviction from kernel OOM, and compressed from incompressible
   workloads. Protect the foreground surrogate, retain negative controls, and
   show actual zRAM usage/recovery. A generic Linux test or TCG speed is not
   Android17 framework/GMS performance proof.
2. Genuine finished product: startup completes; SystemUI, launcher, Play services
   and Store settle; record per-process PSS/RSS, available memory, zRAM physical
   usage, PSI stalls and lmkd/OOM/ANR evidence. Separate first-boot compilation
   from warmed steady state. Keep actual software versions and workload inputs.
3. Physical use: measured launcher/touch responsiveness, app cold/warm launches,
   one simple browser/reader/learning app, repeated app switches, suspend/resume,
   graphics acceleration, sustained operation and battery/temperature. Repeated
   launcher kills, boot loops, ANRs, long memory stalls or software-rendered UI
   mean the useful-device result is not achieved even if a boot screen appears.

Do not invent pass thresholds or throughput before measuring the physical
baseline. A useful single-app result and a smooth multitasking result are
different claims and must be reported separately. zRAM compresses existing RAM
and costs CPU; it does not create equivalent physical RAM.

Official background, not device-specific proof:
[Android low-RAM/Go configuration](https://developer.android.com/guide/topics/androidgo),
[Android memory allocation and zRAM](https://developer.android.com/topic/performance/memory-management),
[lmkd and PSI](https://source.android.com/docs/core/perf/lmkd).
The Go hardware table currently shown on that page reaches Android13; it does
not establish Android17's requirements or this port's performance.
