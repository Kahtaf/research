# Android 17 product input mappings and next-build kit

Question: can the sealed product candidate gain the reviewed touchscreen/key
mappings and use the proven eight-job full-build limit without touching r5?

Status: composition complete. All 25 Linux tests and the actual input audit
pass. Live preflight refused the original running build. No active integration, build launch or
device operations are authorized by this kit. Original staging/kit r1 stay frozen.

Outputs and continuation: inspect source/scripts, inputs, and evidence here.
The new remote candidate will be staging/r2 and the new kit reviewed-build-kit/r2.
Run bounded selection tests, seal, audit actual inputs and verify the native
r5 build is terminal before any separately reviewed integration. PLAN_ONLY default.

See [HANDOFF.md](HANDOFF.md), [REPORT.md](REPORT.md),
[Linux verification](evidence/linux-verification.json), and
[composition receipt](evidence/composition.json). The new sealed kit hash is
`841581a33251c975d19329d03318fb1e43e94dbdfebddcac4cd7d1def742ad70`.
