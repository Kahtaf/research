# Separate complete ARM64 GPIO28 lifecycle kernel

Status: COMPLETE. All four actual compile stages exited 0, essential output checks passed, and downloaded artifacts matched their actual VM hashes. This is a separate compile-proof candidate, with both HAL routes still qualified=false. It does not replace the first physical kernel trial, frozen BMC kernel/probes, e9 physical SD probe, or any product input.

## Provenance and isolation

Baseline: `/srv/android/asus-bmc156-full-kernel-r1`, original source/output left untouched. Baseline Image.gz-dtb SHA256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`; config `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`; DTB `a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77`.

Owned VM prefix: `/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1`, with independent `kernel/` and `out/`. No baseline output objects were reused. The ordinary source copy allocated 864,137,216 file bytes; directory and receipt overhead has a conservative 96 MiB allowance. Only known baseline sources and existing system toolchain are used. Full sources and bulk objects remain on the VM.

Stages: `patches/01-stock-gpio28.patch` restores the stock GPIO28 software contract; `patches/02-resolved-config.patch` selects only AMP_AW8737S y→n and ASUS_P00A_STOCK_SPEAKER_GATE absent→y; `patches/03-lifecycle.patch` is the exact completed independent-review lifecycle repair, SHA256 `fe5059391788124fba3addc389c9eb45d12991800b27ce873a855ea2ccfbac83`. Both new headers were required absent at the appropriate stage. Every patch uses `--batch --forward --fuzz=0 -p1`, and all small-set pre/post hashes match. Eight distinct source paths are changed. `patches/combined-from-bmc.patch` is their exact final aggregate delta; `evidence/pre-post-pins.json` records original/final source identities. No full-tree rehash or manifest export was run.

No excluded PCM-copy patch was accessed, included or retried. The selected routing source `mt_soc_pcm_routing.c` remains byte-identical. No gain, timing, electrical tuning, waveform or amplitude decision was added. Reviewed guards and lifetime protection are retained exactly, with no compile fix.

## Actual compile commands

Common command arguments:

```text
make -C /srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1/kernel \
  O=/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1/out \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ \
  LOCALVERSION=-g717bb3c9e13c-dirty -j1 <targets>
```

Targets run serially: `olddefconfig`; whole translation units `sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.o` and `sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.o`; `dtbs`; then full `Image.gz-dtb` from the fresh output tree. The full build also compiles header-dependent callers and links the actual kernel. Compiler identities must match the baseline receipt, including GCC 13.3.0 and binutils 2.42.

Actual affinity is CPU0, inherited by all build children; make is max-j1. Native AS remains unlimited (`[-1,-1]`), with no AOSP address-space cap. Nice level 10 keeps the extra job lower priority. A single 3,600-second window covers the entire four-stage compile. The supervisor checks only its owned output/tmp/evidence allocation and stops its make process group if the approximately 3 GiB allocation allowance or deadline is exceeded. It neither inspects nor changes the independent Android build, its processes, source/out, caches or locks.

Actual olddefconfig exited0 and resolved exactly to `26c59e0afa3f6438fafea4b5379b898c9b1fcaf05adf1d7e14db93b2e976bd13`. No symbol except the two named audio selections differs from the complete BMC configuration. Thus existing firstboot, network, SoC, BMC156, PSI, zRAM, charging/radio and all other baseline selections are preserved. No virtual configuration is copied.

## Evidence and continuation

`evidence/build-status.json` records exact commands, timestamps, terminal status and exits. `evidence/toolchains.json` binds compiler/tool bytes. Build terminal logs are retained compressed. Essential final verification records actual Image/config/DTB sizes and hashes, appended DTB and embedded config equality, OF GPIO28/0, unchanged resolved USB24 binding/pinctrl, absent AW activation symbols, absent charging DT permission, selected untouched source pins and unchanged baseline image/config/DTB anchors. Numeric DT phandle renumbering caused by deleted audio pin states must be resolved semantically when checking USB references.

No cloud lifecycle or package installation, device/ADB/root, GPIO/mixer/playback, charging/radio, private calibration/key access/upload, product-kernel update or sealed-kit mutation occurred. No new independent review or inherited host suite was run. This work is done by this implementation agent without children.

Read the final status and artifacts receipt before continuing. Do not rerun preparation or launch scripts against the existing prefix. A network interruption is not a restart signal. Do not rerun old source-model suites or treat compile success as fitted electrical identity, physical level, safe amplitude, sound, hardware success or flash/commissioning approval. Future physical/integration work remains separately authorized parent work; retain the existing first physical trial/probe priority.

## Complete delivery

The entire serial compile ran from `2026-11-07T07:20:22.463034+00:00` to `2026-11-07T07:50:31.737616+00:00`, 1809.275 seconds (30 minutes 9 seconds), inside the single 60-minute window. Actual source/object/DTB/full-image commands and exits are in `evidence/build-status.json`; all exit codes are 0. The actual full Image target itself took 29 minutes 47 seconds. No production fix was required.

- `artifacts/Image.gz-dtb`: 7,718,408 bytes; SHA256 `ea567598778060428b55104bbbd2bddca5e36958a8e9b8a5ac93c0dce92dd52b`.
- `artifacts/resolved.config`: 126,521 bytes; SHA256 `26c59e0afa3f6438fafea4b5379b898c9b1fcaf05adf1d7e14db93b2e976bd13`.
- `artifacts/asus-p00a.dtb`: 63,383 bytes; SHA256 `4cb0785f471410db0d56c2cb29b60e52011d0c3cbe18ccc66f9c9621c9379aec`.

Actual uncompressed ARM64 Image remains on the VM: 17,345,024 bytes; SHA256 `222bcb78748274d5f383a0fbb30bc34323a8007e0f6ea69b8fffc08e5dee31f3`. It exactly equals the decompressed local complete kernel's payload. The appended DTB exactly equals the delivered DTB, and embedded IKCONFIG exactly equals the actual delivered resolved config.

The conservative total owned allocation upper bound is 1,545,195,520 bytes, including the source files and a 96 MiB source-directory allowance, below 3 GiB. Compact downloaded artifacts/receipts total 8,131,919 bytes (about 7.76 MiB); all full source, bulk objects and vmlinux remain on the VM. `evidence/local-delivery.json` binds local bytes to `evidence/verification.json`.

The actual DT selects `/soc/mt_soc_codec_name@11220000` with singular extspkamp-gpio cells `[16,28,0]`, resolving phandle16 to `/soc/pinctrl@10005000`, the declared MT8163 GPIO controller. USB24 still resolves to the same controller, pin24/flags0, with the same USB selector pinctrl target and programming. Deleted audio GPIO24 states cause ordinary numeric phandle renumbering in DTB references; raw numeric identity is not required where the resolved node identity is unchanged. `evidence/dt-delta.json` retains the small raw DT differences. The existing charging permission `asus,allow-battery-charging` remains absent.

The first final verification attempt incorrectly demanded whole-kernel absence of the generic name `switch_mode_delay`. ELF FILE-symbol provenance proves the surviving local symbol belongs to the unchanged `accdet.c`, not the codec. The checker was corrected to require absence of AW activation symbols in the actual repaired codec object **and the linked MT8163 audio built-in object**, plus absence of unambiguous AW873-named symbols across vmlinux. The codec lifetime/state/gate symbols are present in vmlinux. `evidence/verification-failure.json`, `evidence/AW-symbol-investigation.txt`, `evidence/linked-audio-selection.txt`, `evidence/symbol-name-collision.json` and `evidence/audio-symbols.json` retain the checker correction and its evidence. No source, config, guard, lifetime protection or kernel artifact was changed for that correction. No build was repeated.

`evidence/pre-post-pins.json` and the original per-stage pins are the exact small source delta identities. The existing six-path untouched source sample remains equal to baseline, including routing, AFE, pinctrl, init, memory reclaim and network core. The original baseline Image/config/DTB hashes were rechecked unchanged at completion. HAL routes remain at their pinned original hash and both `qualified=false` in `evidence/HAL-unchanged.json`. No original fixture, physical probe, product kernel/prebuilt, active product input, sealed kit or independent Android job was modified.

Continuation: this compile proof closes the target-object/DTB/full-kernel build gap for the reviewed repair. Keep this as a separate candidate. Consult the completed independent lifecycle review for its bounded source/host conclusions. Preserve the earlier physical trial and e9 SD probe priority. Any future product integration or hardware qualification remains parent work under its own authorization; no fitted electrical, sound, safe-amplitude or physical success follows from these artifacts. Do not re-run this prefix's preparation/launch scripts. The fixed-transport `python3 -B scripts/status.py` is read-only if current receipt inspection is needed.
