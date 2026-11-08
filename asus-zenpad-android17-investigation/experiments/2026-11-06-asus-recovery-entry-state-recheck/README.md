# Stock recovery-entry state recheck

Question: does the live stock ASUS still have the verified clear recovery request before a supervised recovery test?

Status: two complete 512 KiB captures at 2026-11-07 00:17:49 UTC matched clear-state SHA256 `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`. The pinned established reader confirmed both hashes, staging cleanup and Enforcing restoration. No partition write, clear request or reboot occurred. Evidence: `evidence/host-hash-reader-result.json` and the referenced original reader receipt. Private captures stay under the original spike's ignored mode-0700 directory.

The first tablet-hash method failed before its report; stock has no sha256sum. That source and failure remain under evidence. The current `source/observe.py --observe` delegates only to the established host-hash reader with exact source/ADB pins. It defaults to PLAN_ONLY. The existing helper stages its pinned root binary; this does not claim zero device-file writes.

Continuation: use this bounded observation close to recovery entry if time or state changes. A mismatch or uncertainty stops without automatic clear, retry or inverse. A clear-state snapshot does not establish working USB, supervision, bootability, timing or flash readiness. No raw capture goes to agents or cloud.
