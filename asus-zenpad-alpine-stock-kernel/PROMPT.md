# Paused handoff — read first

Owner paused work on2026-11-09. Start with STATE-AND-RESUME.md and resume only after an explicit request. The original brief below is historical; its autonomous-work instructions do not override the pause. The public Git archive intentionally lacks private inputs and all installable images.

Continuation rule: the owner being away defers physical gates only. Continue independent scoped work over pinned Wi-Fi SSH; a stale goal-tracker blocked flag is not a reason to stop using available tools. Do not ask the owner to rotate the tablet while its unreliable USB port is connected.

Current execution state is in MEMORY.md and reports/CHECKPOINT.md. The prompt below is the original starting brief; its recovery/access descriptions are historical.

# Paste into a new session

Work in `/Users/kahtaf/Documents/workspace/ideas/2026-11-08-asus-alpine-stock-kernel` and follow the parent AGENTS.md. Read README.md, MEMORY.md and UPSTREAM.md first; private/ACCESS.json has historical device access details.

Android17 and Linux4.9 bring-up are parked. Investigate and then implement the newest stable Alpine aarch64 userspace on my ASUS Z380M/P00A_2 using its **own working stock3.18.35 kernel**. I want a lightweight touch dashboard/browser and SSH with small long-lived services; heavy coding/build jobs can stay on the Mac mini.

Start from https://github.com/kaantcp/z380m-alpine (recorded pin7218a276f252a59874ab860683c061fa2b856519). It reports a stock-kernel Alpine desktop, but Wi-Fi is missing. Our stock Android Wi-Fi works and vendor source/firmware evidence is retained. Investigate the stock Wi-Fi startup dependencies rather than assuming a new driver is needed. Our panel is GoodixGT6108, unlike the donor's ELAN panel. Verify the current stable Alpine release and actual old-kernel compatibility.

First inspect the donor and our saved evidence, verify fresh tablet/access/card state, and give a short practical plan. Then pursue one bounded experiment at a time toward a usable Linux shell, Wi-Fi, touch desktop and real browser/service workloads. Prefer a reversible RAM/SD-root proof where possible. Preserve original backups, factory calibration, bootloader and GPT. Do not blindly run the donor's BOOT/SYSTEM installer or old Android17 scripts; recovery currently holds an old diagnostic and the SD card may contain old installation triggers.

Avoid speculative variants, enormous test suites and endless checking. If stuck, consult Opus5.5 first; only if it refuses use Large v2. Use gpt-6.1-sol implementation subagents when useful. Do not repeatedly ask if I am nearby: proceed within the agreed scope and I will hold Power later if needed. No new GCP resources by default. Keep all new supporting files in this folder and private device data out of Git. Preserve evidence distinguishing actual physical success from source/model claims.

Prior investigation archive: https://github.com/Kahtaf/research/tree/main/asus-zenpad-android17-investigation . It explains the failed approaches; do not resume the 4.9 diagnostic ladder.
