# Combined r3 full-product build r6

Question: can the exact reviewed r3 source candidate produce valid Android17 BOOT/SYSTEM?

Status: r6 launched once at 22:25:14 UTC. Reviewed integration completed; native build started at 22:26:03 UTC and ended exit1 at 22:28:00 UTC. The accelerometer BoardConfig path expanded empty, creating `/sepolicy` in genuine Soong variables and a configuration panic. No completed images. The exact one-line fix is staged separately in `2026-11-06-asus-sensor-board-path-fix`; active r6 sources remain preserved.

Outputs: evidence/parent-kit-review.json and eventual native launch/result/source/image records.

Continuation: run `python3 -B source/observe_r6.py` for one bounded observation of the existing native handle. Supervisor PID 1546715 owns the original lifecycle lock; build PID 1548484 was recorded at launch. Inspect terminal receipts and exact failures before taking another action. Never rerun the launcher, delete attempt markers, restart because of quiet logs, or installclean. No tablet operations or physical GO.
