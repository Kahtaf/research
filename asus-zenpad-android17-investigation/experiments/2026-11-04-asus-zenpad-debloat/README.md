# ASUS ZenPad Z380M reversible debloat

Question: Can the connected P00A/P00A_2 tablet be made lighter while preserving all Google components and user data?

Status: Applied and reboot-verified November 4, 2026 after reconnection. All 15 ASUS candidates were disabled for user 0 and remained disabled after reboot (`sys.boot_completed=1`). All installed/enabled/disabled Google package lists are identical to baseline; all previously disabled packages remain disabled. Nova remains the default HOME, Gboard the keyboard, and Chrome the WebView provider. All 13 explicitly retained packages remain enabled. Wi-Fi is enabled and internet ping succeeded. Settings and Nova returned successful activity-launch status. Play Store's first launch timed out during startup; its post-boot recheck returned `Status: ok`. Battery was 74% before execution. No app data was cleared, no package uninstalled, and no root or firmware changes made.

Scope: Disable unused ASUS notes/reminders, weather, photo extras, retail demos, help/log-upload apps and Easy Mode. Preserve every Google package, Nova, Gboard, Chrome/WebView, ASUS Kids Mode, camera/gallery, audio, lock screen, hardware, power services, and the stock ASUS launcher in this first pass. Previously disabled packages remain disabled. No uninstall, data clearing, root, firmware flashing, or automatic reboot.

Important outputs:

- `debloat.py`: serial- and model-checked inventory, apply, and restore commands.
- `restore.sh`: restores exactly this applied run (invoke with `sh restore.sh`).
- `runs/20261104T211525.925216Z/verification.json`: successful post-apply preservation checks.
- `runs/20261104T211525.925216Z/post-reboot-verification.json`: boot, package preservation, defaults, and connectivity verification.
- `runs/20261104T211525.925216Z/app-launch-checks.json` and `play-store-recheck.json`: launch results, including initial Play Store startup timeout and successful recheck.
- `runs/`: created during execution; package baselines, per-package original states, change journal, and verification results. Contains device identifiers; keep local.

Continuation after reconnecting and unlocking the tablet:

```sh
python3 debloat.py inventory
python3 debloat.py apply
```

Every apply run saves its state before changing packages and prints the exact restore command. Restore accepts that run directory:

```sh
python3 debloat.py restore --run runs/RUN_DIRECTORY
```

Restore only handles packages attempted by that run, returning their original enabled/default state. It also handles a package interrupted between the disable command and journal completion.

Remaining optional user checks: exercise Home/Back/Recents, keyboard input, audio, camera/gallery, Play Store downloads, and an app using WebView. Activity-launch success and package-state checks do not establish that authenticated Store downloads or every app flow works. No performance benchmark or battery-life comparison was conducted.

Follow-up assessment: `assessment.json` records a live post-boot check. All 15 candidates remain disabled and all 13 retained packages remain enabled. The original Google package states are preserved; one additional enabled Google package (`com.google.android.verifier`) appeared after reboot, so the strict whole-list equality check now reports false. No Google mutation commands were issued; automatic provisioning/update is an inference. About 662 MiB RAM was available in the recorded sample, with 3.7G storage free. Google Play services used 24–27% aggregate CPU over two three-second process samples; a subsequent thread sample identified GoogleLocationS as the largest individual thread. This is mixed post-boot activity, not an idle benchmark or proof of a regression. No additional debloat was applied. ASUS's official support page lists WW_5.3.20 (2018-08-28) as the newest firmware, matching the tablet. No verified newer Android ROM for Z380M/P00A was located.

Second pass, 5 November local / 6 November UTC: explicit authorization to remove further optional bloat. `runs/20261106T025111.159949Z` reversibly disabled AppCloud promotions (`com.ironsource.appcloud.oobe.asus`) and ASUS Game Broadcaster (`com.asus.gamewidget`). Both had optional recommendation/game-broadcast components and background receivers; neither was a hardware service. This brings the total to 17 disabled candidates. Google installed/enabled/disabled lists are exactly unchanged from this pass baseline; all retained packages/defaults pass. No app data or APK was deleted. No measured speedup is claimed.
