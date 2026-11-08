# Exact Linux 4.9 recovery probe observation

Question: can the frozen combined probe r2 be observed without confusing report
transport, successful measurements, normal return, and recovery restoration?

Status: implemented; 15 offline test methods pass, including fault subcases and
actual frozen image/stock-backup hash checks. No device actions,
writer, physical boot claim, or flash approval. This is a separate observer; the
existing stock-kernel-only writer and observer remain unchanged.

`source/observer.py` accepts only the frozen r2 image, exact diagnostic identity,
and a fresh same-run physical USB pin. Targeted ADB calls recheck inventory before
and after and use the current transport ID. Missing/error/truncated measurements
are recorded separately. Directory listings cannot prove completeness because
the frozen collector does not report directory errors. Charging safety and any
hardware readiness are explicitly outside this acceptance result.

Run offline tests with `python3 -B -m unittest discover -s tests -v` from this
folder. CLI defaults to PLAN_ONLY. `--execute` enables the explicitly selected
read-only phase; there are no reboot, root, mount, or partition-writing commands.
The first physical 4.9 boot still requires nearby physical fallback and a separate
reviewed writer. Do not reuse old stock-control pins or claim `--supervised` while
the user is away.

Continuation: finish offline tests and negative replay, then prepare a concrete
supervised run with a new run UUID. Start observation while stock Android is
present, before the separate writer/recovery entry. Pin validity is three minutes
at observation start; observation is bounded to seven minutes. Full acceptance
also requires a fresh full stock recovery readback produced by the parent after
the observed return. A local readback file proves its bytes, while its physical
origin remains the parent's responsibility; the observer never invents that
provenance. Keep the original failed/partial evidence.

## Parent commands

Offline operations (no device contact):

```
python3 -B source/observer.py verify-image
python3 -B source/observer.py validate-report --report <captured-report.txt>
python3 -B source/observer.py pin
```

For a separately qualified supervised trial, use one freshly generated canonical
UUID consistently. Start the observer in stock Android before recovery entry;
the initial transport must still match the pin. Each output directory must be new
and inside this spike.

```
python3 -B source/observer.py pin --execute --run-id <uuid> --out evidence/<uuid>/pin
python3 -B source/observer.py observe --execute --run-id <uuid> --pin evidence/<uuid>/pin/pin.json --out evidence/<uuid>/observe
```

Observation deliberately returns exit 2 even after a valid report and normal
return: stock recovery restoration is still outstanding. After the parent has
actually restored stock recovery and captured a fresh complete p10 readback:

```
python3 -B source/observer.py finalize --execute --run-id <uuid> --pin evidence/<uuid>/pin/pin.json --observation evidence/<uuid>/observe/observation.json --readback <actual-post-return-full-p10-readback.bin> --out evidence/<uuid>/final
```

Do not supply an old backup copied into a new file as a readback. A local file's
hash and timestamps do not independently prove its device origin. The parent
must preserve the actual reader/writer journal alongside the final receipt.
Even final acceptance is only diagnostic plus stock recovery restoration;
`hardware_ready` stays false and does not authorize the full OS installation.

## Review findings addressed

- F1: exact r2 whole-image and padded hashes bind every byte, including all
  reviewed kernel/DT/ramdisk/policy/helper/key inputs. New serial/model/product
  profile leaves stock-only tooling unchanged.
- F2: fresh same-run preflight, exact per-operation inventory checks, strict
  framing/token parsing, explicit failure/partial states, and separate stock
  readback verification. Stock return alone never succeeds.
- F3: required identity/kernel/enforcing/USB/mount observations must succeed.
  Optional read errors remain unavailable; all directory listings remain
  unverified because r2 cannot report their collection status. No blanket
  hardware, charging, or guaranteed timer-return claim is made.

Remaining: physical run, separate exact-candidate writer/restoration integration,
and nearby fallback. The image is unchanged. This host-only fix requires no new
kernel or ramdisk build.
