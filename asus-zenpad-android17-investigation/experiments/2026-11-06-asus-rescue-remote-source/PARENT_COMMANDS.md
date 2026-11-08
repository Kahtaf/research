# Parent-only continuation

Run from this spike. These commands were not run against a target. Defaults do not contact either target or source.

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-rescue-remote-source
python3 -B source/verify_handoff.py
python3 -B -m unittest discover -s tests -v
python3 -B source/source_cli.py samples --profile userdata-pristine
python3 -B source/parent_remote.py write --source-profile userdata-pristine
python3 -B source/build_manifest.py --review artifacts/original-pair-remote-review.PENDING.json
```

A later source-only full preflight/export, if useful, reads every byte of the actual fixed source and writes only a small receipt/table locally. Use a fresh output name. It neither opens a target nor makes its closed source session reusable:

```sh
python3 -B source/source_cli.py preflight --profile userdata-pristine \
  --read-only-execute --output evidence/parent-fresh-userdata.SOURCE.json
```

For manifest construction, the original review schema is unchanged: each row has exactly `path` and `sha256`, with the original 2/4/5 ordered roles and all original approval booleans. Remote source paths use `source://stock-system` or `source://userdata-pristine`; local originals use the fixed rollback bundle paths. Source receipts are evidence, not replacement approval inputs. `artifacts/original-pair-remote-review.PENDING.json` deliberately fails approval validation. Do not flip its pending approval merely to make a build pass. Current unbound install roles prevent five-role manifest generation.

With an independently completed review, the parent can generate a binary and SOURCE evidence without a local SYSTEM/data copy. This does not repackage, arm or deploy any recovery:

```sh
python3 -B source/build_manifest.py \
  --review "${PARENT_COMPLETED_REVIEW:?review path required}" \
  --output "${PARENT_NEW_MANIFEST_OUTPUT:?new path required}" \
  --build-reviewed-manifest
```

The following is a **future parent command template**, not an approved physical operation. The parent supplies current reviewed values after its physical qualification and approved arming. Retain `--stop-after-chunks` only when the parent deliberately selects a bounded partial trial; omission requests complete transmission/readback/commit. Run without `--execute` first to inspect PLAN_ONLY. No timing or reboot option exists.

```sh
python3 -B source/parent_remote.py write \
  --adb "${PARENT_PINNED_ADB:?absolute binary path required}" \
  --adb-sha256 "${PARENT_ADB_SHA256:?reviewed binary hash required}" \
  --transport-id "${PARENT_CURRENT_TRANSPORT_ID:?current authenticated transport required}" \
  --contract "${PARENT_APPROVED_CONTRACT:?approved contract required}" \
  --contract-sha256 "${PARENT_CONTRACT_SHA256:?reviewed contract hash required}" \
  --manifest "${PARENT_ARMED_MANIFEST:?exact deployed manifest required}" \
  --image-index 4 --source-profile userdata-pristine \
  --image-sha256 1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1 \
  --source-receipt "${PARENT_NEW_SOURCE_RECEIPT:?new receipt path required}" \
  --evidence "${PARENT_NEW_WRITE_EVIDENCE:?new journal path required}"
```

Only the parent may append `--execute` to its qualified command. That invocation opens the fixed source, fully verifies the held FD against the reviewed manifest, then checks features and opens exactly the current `-t … shell -T rescue-v1`. It does not accept a previously saved SOURCE receipt as preflight.

For stock SYSTEM inverse, use role0 and its pinned hash. Prefer `--image /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/system.img` instead of `--source-profile`; this preserves cloud-independent rollback. Remote fallback is `--source-profile stock-system`. Select `--inverse-from-image-index 2` only when explicitly reconciling an uncertain install SYSTEM to original SYSTEM. BOOT uses role1, fixed local `boot.img` and its exact stock hash, subject to unchanged target SYSTEM-first rules. Do not infer an inverse role or offset from a lost acknowledgement.

On any source/target failure: do not automatically retry, change p10, advance role, reuse a prepared source, or resume at an offset. Preserve the journal. A later explicit parent operation must establish idle status and reconcile actual target chunks with the pinned manifest/p10; a fresh source preflight runs before that later target shell. The adapter provides no writer teardown, device reboot or transport discovery command.
