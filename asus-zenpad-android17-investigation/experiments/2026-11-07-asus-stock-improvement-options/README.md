# Stock Android7 improvement fallback

Question: what can the Android17 port effort contribute if the newer kernel cannot be brought up? Status: research/options only; no stock settings, apps, kernel or firmware changed for this side question.

The strongest practical path is the existing stock kernel/hardware stack plus selective reversible debloating, lighter supported apps/UI, background-work reduction, and measured memory tuning. Keep Play services/Play Store and Google components per the owner. Check current zRAM, memory pressure and app reloads before changing low-memory killer/swap settings; supported knobs can often be tuned without a kernel rebuild. Do not copy modern SDK37 memory defaults or hardware patches blindly to Android7.

Project-specific lessons: stock USB uses legacy android_usb (configfs second bind fails EBUSY); its existing driver now physically exposed the readonlyRAM report. Stock RAM PID1/custom recovery path works. Existing on-demand root and exact backups enable bounded reversible stock changes. Main battery versus cover, amplifier GPIO28 versus erroneousGPIO24, radio calibration containers and driver ABI facts help avoid damaging changes, not necessarily improve alreadyworking stock drivers. The new4.9 fixes target its changed ABI and aren't evidence of stock faults.

A custom stock-based firmware could provide a cleaner launcher/app set, compatible updated components, selected patches and measured tuning while retaining hardware compatibility. Kernel/Android7 framework patches are technically possible, but exact public ASUS3.18.22 source is not the shipped3.18.35 revision; a rebuilt kernel is another bringup effort. Select bug/security backports are not full current security coverage and must not be advertised by falsifying security patch/API levels.

A kernel update alone cannot supply newer Android framework/Bionic/WebView APIs required by modern apps. Example: Chromium's official Nougat deprecation sets Chrome119 as last Nougat version and120 minimumSDK26. A modern-looking UI is easier than current app compatibility. Remote applications/streaming from a newer computer are another way to expose modern functionality while keeping a light tablet client, subject to client compatibility; no product selected/researched here.

Sources: historical AOSP lowRAM tuning https://android.googlesource.com/platform/docs/source.android.com/+/3587851127f0703f29ac921d44c8696315a693b0/en/devices/tech/perf/low-ram.html ; official Chromium Nougat support statement https://groups.google.com/a/chromium.org/g/chromium-dev/c/B9AYI3WAvRo/m/tpWwhw4KBQAJ . These support general tuning mechanisms and compatibility limits, not measured gains on this tablet.

Continuation: if this fallback is selected, begin with current package/settings/memory inventory, make a few reversible changes, and compare actual app switching/launch/reload behavior. No broad test campaign or new stock kernel build first. Android17 remains the current objective; this note is a contingency, not a scope replacement.

## Actual read-only stock snapshot

2026-11-07 20:38UTC, same verified stock boot, no root/configuration change: MemTotal2000192KiB (~1.91GiB kernel-visible), MemAvailable925052KiB (~903MiB), zRAM swap1000092KiB (~977MiB), swapused56340KiB (~55MiB). CPU0-1online at this instant; governorinteractive. Blank ro.config.low_ram. zRAM disksize sysfs read unavailable; actual/proc/swaps is direct evidence that stock zRAM is already enabled. This idle snapshot is not a benchmark or peak-pressure claim. More swap is not automatically an improvement; reducing unnecessary background work and testing actual app switches is the better first tuning target. See stock-memory-snapshot.json.
