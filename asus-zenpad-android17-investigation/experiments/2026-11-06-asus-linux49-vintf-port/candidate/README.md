# Candidate scope

`checkvintf-inputs.patch` stages only the corrected test command: copied installed metadata/APEX and the full resolved config proven embedded in the exact compiled kernel. `checkvintf-command.json` is the concrete command that ran, with expected current failure and input pins.

`REJECTED-target7-diagnostic.patch` documents the single manifest change exercised on an owned copy to test the consequences of selecting the oldest installed FCM. It failed. Do not integrate it.

There is no approved legacy product/kernel matrix patch. Applicable genuine 4.9 requirement provenance and a justified retrofit target remain unresolved. No no-op/empty matrix or checker bypass is provided. See `../REPORT.md`.
