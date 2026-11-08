# Latest Android feasibility audit: ASUS Z380M / P00A

Question: What is the most credible experimental path to the newest Android on the connected ASUS ZenPad 8.0 Z380M, while retaining a recoverable tablet and eventually Google Play support?

Status: Audit complete; conditional go for an experimental Android 17 / LineageOS 24 port. See [REPORT.md](REPORT.md). No custom ROM has been built or flashed. Target the newest published Android source first; do not silently settle on Android 11. Older MT8163 work is a reference and potential diagnostic baseline, not the end goal. This spike is separate from the completed ASUS debloat.

Scope: Read-only tablet hardware/kernel/vendor collection, original ASUS source inspection, comparison with current MT8163 kernels and Android platform requirements, bounded source/build experiments, and an evidence-backed go/no-go report. No rooting, unlocking, rebooting into flashing modes, partition writes, or firmware flashing during this audit.

Done means: a reproducible inventory, verified source provenance/completeness, explicit evidence for the main compatibility gaps, at least one concrete source/build probe, and a ranked experiment plan targeting the newest Android with known uncertainties distinguished from demonstrated blockers. A source build is not evidence that an image boots.

Workflow:

1. Capture connected hardware, running kernel/config, partitions, boot state, and vendor library inventory without reading personal app data.
2. Download the ASUS source archive; inspect it and community MT8163 projects at pinned revisions.
3. Probe buildability and assess kernel interfaces, GPU/display, Wi-Fi, HALs, partition limits, recovery, and host build resources.
4. Write the verdict and concrete next experiments, including stopping conditions and recovery requirements.

Outputs:

- [REPORT.md](REPORT.md): verdict, hardware/source evidence, route ranking, acceptance gates and continuation plan.
- [routes.html](routes.html): compact comparison and experiment sequence.

- `scripts/`: repeatable collection and analysis tools.
- `evidence/`: raw command results and structured findings. Device identifiers may appear; keep local.
- `sources/`: reference source trees and provenance.
- `downloads/`: original archives and checksums.
- `decisions.tsv`: decisions, evidence and outcomes.

Continuation: Read REPORT.md and decisions.tsv first. Start the offline ASUS 4.9 bring-up as a new spike with its own README, using the pinned sources in the report. Re-run collection only for the explicitly pinned ASUS serial. Do not use any output as a flashable image. Firmware changes require a separately reviewed experiment with backups and a proven restore path.

Follow-up: REPORT.md begins with corrections discovered by the actual kernel compile, including an empty live-DT pull and incomplete BPF candidate. Continue in ../2026-11-05-asus-mt8163-kernel-bringup.
