# Linux 4.9 microSD report spike

Question: can the existing recovery Linux 4.9 kernel produce fresh PID1 uname boot proof on an independently verified removable microSD when USB DATA is unavailable?

Status: implemented and built as one static ARM64 candidate; three focused mock check groups and package layout passed. No physical boot, SD hardware, persistence or automatic reboot verification. Parent alone prepares the existing card and decides deployment. Existing spikes/transports are preserved.

Important outputs:

- `artifacts/candidate.img`: 8,044,544-byte candidate, SHA-256 `505707610e035ea3b1b7364e5ad75ce1cf2396eca9b64e378c3b90150df6853d`.
- `card-preparation/PROBE.ID`: exact 37-byte marker for run `dbbb6afb-dd70-4c35-961e-9c977d7164a8`; fresh output is `PROBE.TXT`.
- `HANDOFF.md`: contract, parent preparation, failure behavior, padded-p10 hash/location and physical acceptance.
- `source/init.c`, `SOURCE.diff`: implementation and baseline delta. The other packaging modules/templates are copied unchanged except the ramdisk directory/config requirements in `package_probe.py`.
- `evidence/manifest.json`, `evidence/build-log.json`: actual candidate and focused build evidence. Padded p10 remains in the isolated builder prefix.

Continuation: follow HANDOFF.md for parent preparation/physical trial. No formatting, repair, deployment writer or transport adapter is included. `scripts/local_driver.py` uses only the baseline fixed SSH helper and `/srv/android/asus-linux49-microsd-report-20261107`: `setup` refuses an existing prefix; `sync` restages this spike; `build` performs the small build; `fetch` retrieves the small candidate/evidence. A build has already succeeded, so repeating it is unnecessary for the current handoff.
