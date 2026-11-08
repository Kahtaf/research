# R3 parent commands — review first; no execution by implementation agent

These are individual parent-operated steps, not an unattended script. The first
physical 4.9 boot remains held. **Do not assert supervision or physical fallback
while the user is away.** A static review receipt and the anticipated 23:03 UTC
return do not establish presence. This CLI never enters recovery or returns the
device to stock; parent supervises those physical actions separately.

From the ideas workspace, the offline checks are runnable now:

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-linux49-r3-transport
python3 -B tests/run_tests.py
python3 -B source/probe_transport.py verify-local
python3 -B source/probe_transport.py plan
python3 -B source/probe_transport.py install
python3 -B source/probe_transport.py restore
```

Review `evidence/implementation.diff`, `profile.json`, `REPORT.md` and
`evidence/code-receipt.json`. The exact code-bundle digest below is the SHA256 of
the compact sorted JSON mapping in that receipt, not the hash of the formatted
receipt file. It includes adapter, adapted base, profile and new R3 observer.
Any change requires new review; do not change code during an active run.

After actual review, parent may prepare these shell variables offline:

```sh
PROBE_ROOT=/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-linux49-r3-transport
OBSERVER_ROOT=/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-linux49-r3-transport
PROFILE_REVIEWED=1729116fe9f302052d84589805b8ea665c2317e5a3a734675baabe320fc7ceca
CODE_REVIEWED=f9aa8238d9d5d09c5d82d8ad8fb5c557a5d245fae819f93194208ac12608a32e
RUN_ID="$(python3 -B -c 'import uuid; print(uuid.uuid4())')"
```

Use this one UUID throughout; do not regenerate it in a second terminal. Keep
phase outputs and the original pin. The following commands contact the target
and are only for the parent's later supervised session with nearby fallback.
Existing backup work must be terminal and competing mutations excluded.

1. Capture a fresh exact-stock authenticated **USB** pin, with the device in
   stock Android and the pinned authenticated Wi-Fi endpoint already available:

```sh
python3 -B "$OBSERVER_ROOT/source/observer.py" pin --execute \
  --run-id "$RUN_ID" --out "$OBSERVER_ROOT/evidence/$RUN_ID/pin"
```

2. Start the read-only observer in another parent-controlled terminal using the
   same variables, while stock Android is still present. Leave it observing
   during install and later manual entry. Its deliberate exit 2 after a good
   report and stock return means restoration verification remains outstanding.

```sh
python3 -B "$OBSERVER_ROOT/source/observer.py" observe --execute \
  --run-id "$RUN_ID" --pin "$OBSERVER_ROOT/evidence/$RUN_ID/pin/pin.json" \
  --out "$OBSERVER_ROOT/evidence/$RUN_ID/observe"
```

3. Install the one frozen probe. These flags are truthful live attestations,
   not conclusions supplied by the implementation agent:

```sh
python3 -B "$PROBE_ROOT/source/probe_transport.py" install --execute \
  --run-id "$RUN_ID" --pin "$OBSERVER_ROOT/evidence/$RUN_ID/pin/pin.json" \
  --reviewed-profile-sha256 "$PROFILE_REVIEWED" \
  --reviewed-code-sha256 "$CODE_REVIEWED" \
  --parent-reviewed --supervised --physical-fallback-present
```

The install pin must remain within 180 seconds through candidate dispatch.
The observer has a 420-second observation window from startup. Do not begin a
physical trial if the observer has failed/expired. Inspect the returned evidence
and full candidate readback before the parent's separate manual entry decision.
The CLI does not issue that decision or a reboot command.

4. After actual stock return, capture a new same-run USB pin. A changed transport
   ID is normal across reboot, but physical USB topology must remain the same.
   If Wi-Fi is unavailable, stop and let parent separately regain the authorized
   transport; this code neither reconnects nor re-enables it.

```sh
python3 -B "$OBSERVER_ROOT/source/observer.py" pin --execute \
  --run-id "$RUN_ID" --out "$OBSERVER_ROOT/evidence/$RUN_ID/returned-pin"

python3 -B "$PROBE_ROOT/source/probe_transport.py" restore --execute \
  --run-id "$RUN_ID" --pin "$OBSERVER_ROOT/evidence/$RUN_ID/returned-pin/pin.json" \
  --reviewed-profile-sha256 "$PROFILE_REVIEWED" \
  --reviewed-code-sha256 "$CODE_REVIEWED" \
  --parent-reviewed --supervised --physical-fallback-present
```

Restore is allowed even if the diagnostic report failed, provided the install
completed cleanly and healthy exact stock has returned. It writes at most one
exact stock inverse; if p10 is already stock it only verifies. On uncertainty,
stop and preserve evidence. There is no retry command. Do not change UUID to
conceal an uncertain run.

5. Finalize only after a valid report, observed stock return, and clean actual
   restore/readback. The adapter selects the capture from the journal; never
   pass or copy a backup as a capture. A new pin for finalization ensures fresh
   current checks, while the original pin remains bound to the trial.

```sh
python3 -B "$OBSERVER_ROOT/source/observer.py" pin --execute \
  --run-id "$RUN_ID" --out "$OBSERVER_ROOT/evidence/$RUN_ID/final-pin"

python3 -B "$PROBE_ROOT/source/probe_transport.py" finalize --execute \
  --run-id "$RUN_ID" --pin "$OBSERVER_ROOT/evidence/$RUN_ID/final-pin/pin.json" \
  --observation "$OBSERVER_ROOT/evidence/$RUN_ID/observe/observation.json" \
  --reader-journal "$PROBE_ROOT/evidence/runs/$RUN_ID/restore/state.json" \
  --reviewed-profile-sha256 "$PROFILE_REVIEWED" \
  --reviewed-code-sha256 "$CODE_REVIEWED" \
  --parent-reviewed --supervised --physical-fallback-present
```

Finalization is within the observer's 1200-second original-pin horizon. A valid
restore remains useful even if diagnostic acceptance is impossible or expired.
Read `evidence/runs/<uuid>/finalize/acceptance.json` and preserve all genuine
command journals. Even accepted diagnostics plus restoration keep
`hardware_ready=false`; they do not authorize Android 17 installation.

If restoration finished before the observer recorded return, or a separate
fresh post-return capture is needed, the explicit **read-only** phase below
makes a new full p10 capture. It requires a fresh current same-run pin (use a new
observer pin output directory, not an overwritten one). An incomplete/uncertain
restore blocks this phase. It will refuse non-stock bytes and never repair them.

```sh
python3 -B "$OBSERVER_ROOT/source/observer.py" pin --execute \
  --run-id "$RUN_ID" --out "$OBSERVER_ROOT/evidence/$RUN_ID/readback-pin"

python3 -B "$PROBE_ROOT/source/probe_transport.py" readback --execute \
  --run-id "$RUN_ID" --pin "$OBSERVER_ROOT/evidence/$RUN_ID/readback-pin/pin.json" \
  --reviewed-profile-sha256 "$PROFILE_REVIEWED" \
  --reviewed-code-sha256 "$CODE_REVIEWED" \
  --parent-reviewed --supervised --physical-fallback-present
```

Then use `.../$RUN_ID/readback/state.json` as `--reader-journal` in step 5.
Determine this before invoking finalization: phase directories are exclusive,
and the tool does not resume a failed finalization. No reader accepts a local
file as proof of physical origin. Local journal verification cannot replace
parent supervision or independently authenticate the device's physical return.

The old R2 entry remains quarantined and its published old bundle digest remains stale. Do not use its observer or profile. R3 observer standalone `finalize --execute` is deliberately refused: finalization must go through the transport adapter and its actual same-run root-read/Wi-Fi-pull journals. The observer's internal byte assessor alone does not establish capture provenance.

Reproduce the metadata repair offline, without touching the parent's artifact:

```sh
python3 -B "$PROBE_ROOT/source/reproduce.py" \
  --out "$PROBE_ROOT/evidence/reproduction-parent-$(date -u +%Y%m%dT%H%M%SZ)"
```

Use a new output directory each time. This copies only the 8.9 MB rebuilt probe and small receipts, never SYSTEM/data. The original builder and metadata helpers are pinned before import. Parent should compare `receipt.json` and the new image with `evidence/reproduction/receipt.json` and the fixed source image.
