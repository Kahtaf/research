# A49PM1 bounded present / ADC / prepare protocol

This observational append is 6,208 ASCII bytes after the unchanged 20,544-byte clock/switch/work/power layouts. Combined capacity is 26,752 bytes. cap_init checks the actual OEM console's remaining capacity before capture writes, header log_size append, or release-published readiness. No mapping, DT reservation, physical address, old layout or old decoder changes.

Offsets relative to this append:

| Offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 64 | A49PM1 fresh UUID identity |
| 64 | 192 | generation, total, first/last retained, wraps, count, reserved0, runtime nr_cpu_ids1; generation tail at160 |
| 256 | 64 | sticky aggregate / guard / busy / admission / overflow loss |
| 320 | 64 | UUID begin guard |
| 384 | 3456 | 6 ring rows, 576 bytes each |
| 3840 | 576 | latest stage |
| 4416 | 576 | latest present invocation stage |
| 4992 | 576 | latest ADC invocation stage |
| 5568 | 576 | latest prepare invocation stage |
| 6144 | 64 | UUID end guard |

Each row begins VA49M plus a two-digit slot, then29 fixed16-digit lowercase hexadecimal fields, spaced17 bytes apart from offset9. Sequence repeats at552; newline575; all unused padding is ASCII space. Initial zero rows are valid canonical empty rows. Fixed snapshots and their ring duplicates must agree except slot. Metadata generation is total+1. Ring first=max(1,total-5), last=total, wraps=floor((total-1)/6), count=min(6,total). Normal wrap is a finite horizon, not loss. Overflow before total could reach U64_MAX is sticky and terminal.

Every commit invalidates its first byte to PoC, writes payload and matching generation tail, cleans the full row to PoC with the linked dsb sy, then publishes V last with a final clean. Interrupted row/header, stale snapshot, malformed padding, UUID/guard fault, or any sticky loss is UNKNOWN STOP. The first publication order is ring, category snapshot, latest stage, metadata; a mid-update capture is rejected conservatively.

Fields in exact order:

`sequence`, `token`, `code`, `raw_cntvct`, `pid`, `parent_token`, `channel`, `samples`, `sample`, `poll`, `status`, `preempt`, `context`, `capture_anchor`, `switch_anchor`, `work_anchor`, `power_anchor`, `property_token`, `property_seq`, `property_raw`, `body_token`, `body_phase`, `work`, `psy`, `callback`, `property_enum`, `entry_raw`, `entry_seq`, `caller`.

Status is a32-bit original int result or an explicit error/branch result; 0x80000000 denotes no status supplied by that stage (a real INT_MIN would be indistinguishable, so cannot be promoted to a known status). sample/poll=0xffffffff means not applicable. No present output bit, raw CHR_CON7, ADC/raw/mV, delay/busy bitfield, register output, battery output, calibration or private value is encoded. Channel and requested sample count are function inputs; the prepare child inherits them from its actual caller-local ADC identity. Readiness branch stages do not repeat any original READ_ONCE. Branch markers occur within the original already-computed branch, never re-evaluate raw conditions.

Each invocation has a stack-local pair token, entry raw counter and sequence. Prepare alone has an instrumentation-only parent parameter, because the original static helper has exactly one source caller. Exported present/ADC signatures are unchanged. Each call's return-site PC is an immutable numeric source-route identity; exact ELF BL+4 sites are pinned in linked-capture.json. New source hooks pass no driver payload pointers to the recorder. No global active owner, worker assumption, active-call map, new lock held across an operation or unbounded storage exists.

The independent PMIC publication raw trylock is nonblocking and briefly IRQ-saving. It never acquires pmic_adc_mutex, pmic_adc_lock, regmap, scheduler, trace_lock, ps_lock or any earlier recorder lock. It performs fixed encoding/memory/cache operations, original task/CPU/context reads, read-only old anchors, and one raw CNTVCT. No printk, timekeeping, allocation, sleep, explicit scheduling, indirect/driver calls or hardware access is introduced by the recorder. Its raw unlock can perform ordinary preemption after releasing the recorder lock; that belongs to the capture gap. An original spin/mutex can surround a hook, but the new lock/IRQ mask has ended before the next original primitive begins. There is no reverse edge from publication into an original lock. Actual preempt/IRQoff/task/hardIRQ/softIRQ context is captured before publication; nonzero preemption/atomic/IRQoff alone is admitted. Only the existing single-runtime-CPU/NMI admission limits apply. Task context limits attribution only, not stage recording.

At an outer entry the recorder may copy the already-published old PS latest-property ASCII snapshot while runtime UP and its own short IRQ mask exclude old writers. It only copies a pending code40 snapshot with matching actual task PID and coherent entry token/sequence. Another task, IRQ, returned property or overwritten/nested context may prevent a candidate association; that is UNKNOWN. Prepare copies its actual parent's immutable fields. Subsequent steps keep their own local identity despite interleaving. Old PS semantics are not changed.

The combined decoder invokes all four unchanged old decoders, validates each append, finite local pairs and stage paths, then requires the old exact selected work/body/property join. Internal attribution requires fresh actual PID/work/body/property tokens and sequence/raw/switch/work/PS anchors, exact supply identity, named callback battery_get_property from the genuine map, property batt_vol from actual configured enum, direct compiled caller BL+4, and ADC channel6/samples5. Historical PID119/work66/body61/property89 are never constants in this join. Prepare additionally must join its actual ADC parent at PREPARE_CALL_PRE. An unrelated latest category/worker/function is UNKNOWN for attribution, while admitted broad old facts remain returned in old_target_facts. Numeric pointer fields in raw decode are parent-private; symbolize_pmic.py emits the map-verified names and status only.

Stages:

| Code | Checkpoint | If the last retained checkpoint |
|---:|---|---|
| 1 | `PRESENT_ENTRY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 2 | `PRESENT_READINESS_PRE` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 3 | `PRESENT_READY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 4 | `PRESENT_READ_PRE` | existing pmic_read_interface(CHR_CON7) dispatch through post publication |
| 5 | `PRESENT_READ_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 6 | `PRESENT_DETECTOR_UNSUPPORTED` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 7 | `PRESENT_NOT_READY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 9 | `PRESENT_RETURN` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 20 | `ADC_ENTRY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 21 | `ADC_ARGUMENTS_VALID` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 22 | `ADC_ARGUMENTS_REJECTED` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 23 | `ADC_READINESS_PRE` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 24 | `ADC_READY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 25 | `ADC_NOT_READY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 26 | `AWAKE_PRE` | existing __pm_stay_awake dispatch through post publication |
| 27 | `AWAKE_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 28 | `MUTEX_LOCK_PRE` | existing mutex_lock(pmic_adc_mutex) dispatch through post publication |
| 29 | `MUTEX_LOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 30 | `PREPARE_CALL_PRE` | existing prepare call through return publication; use joined prepare substage if retained |
| 31 | `PREPARE_CALL_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 32 | `VBUF_CONFIG_PRE` | existing VBUF pmic_config_interface dispatch through post publication |
| 33 | `VBUF_CONFIG_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 34 | `TRIGGER0_CONFIG_PRE` | existing trigger0 pmic_config_interface dispatch through post publication |
| 35 | `TRIGGER0_CONFIG_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 36 | `TRIGGER1_CONFIG_PRE` | existing trigger1 pmic_config_interface dispatch through post publication |
| 37 | `TRIGGER1_CONFIG_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 38 | `UDELAY300_PRE` | existing udelay(300) dispatch through post publication |
| 39 | `UDELAY300_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 40 | `POLL_READ_PRE` | existing poll pmic_read_interface dispatch through post publication |
| 41 | `POLL_READ_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 42 | `POLL_READY_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 43 | `POLL_WAIT_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 44 | `POLL_SLEEP_PRE` | existing poll usleep_range dispatch through post publication |
| 45 | `POLL_SLEEP_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 46 | `POLL_TIMEOUT_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 47 | `SAMPLE_COMPLETED` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 48 | `OUT_MUTEX_UNLOCK_PRE` | existing mutex_unlock dispatch, normal unlock preemption and post publication |
| 49 | `OUT_MUTEX_UNLOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 50 | `RELAX_PRE` | existing __pm_relax dispatch through post publication |
| 51 | `RELAX_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 59 | `ADC_RETURN` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 60 | `PREPARE_ENTRY` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 61 | `PREPARE_SPIN_LOCK_PRE` | existing spin_lock_irqsave(pmic_adc_lock) dispatch through post publication |
| 62 | `PREPARE_SPIN_LOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 63 | `PREPARE_DELAY_READ_NOLOCK_PRE` | existing prepare delay pmic_read_interface_nolock dispatch through post publication |
| 64 | `PREPARE_DELAY_READ_NOLOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 65 | `PREPARE_BUSY_READ_NOLOCK_PRE` | existing prepare busy pmic_read_interface_nolock dispatch through post publication |
| 66 | `PREPARE_BUSY_READ_NOLOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 67 | `PREPARE_CONFIG_NOLOCK_PRE` | existing prepare pmic_config_interface_nolock dispatch through post publication |
| 68 | `PREPARE_CONFIG_NOLOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 69 | `PREPARE_SPIN_UNLOCK_PRE` | existing spin_unlock_irqrestore, ordinary unlock preemption and post publication |
| 70 | `PREPARE_SPIN_UNLOCK_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 71 | `PREPARE_ERROR_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 72 | `PREPARE_READY_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 73 | `PREPARE_WAIT_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 74 | `PREPARE_SLEEP_PRE` | existing prepare usleep_range dispatch through post publication |
| 75 | `PREPARE_SLEEP_POST` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 76 | `PREPARE_TIMEOUT_BRANCH` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |
| 79 | `PREPARE_RETURN` | Source checkpoint through its next checkpoint/caller continuation; no unique blocking primitive inferred. |

The PRE interval includes hook return, ordinary preemption, original dispatch/primitive, and POST-hook entry/publication. Code69 especially includes normal spin-unlock IRQ restoration/preemption; code48 similarly includes mutex-unlock preemption. Return checkpoints9/59/79 precede the C epilogue; ADC31 is the separate prepare-return observation. Original bounded100-poll and5-sample loops do not guarantee a wallclock bound on their underlying primitives or scheduling. Missing post proves neither permanent nonreturn, deadlock, holder, generic clock failure nor source cause. The old cached ADC+340 epoch is unestablished and is not used.

Parent owns one physical exposure, complete-console collection, fresh identity/full-p10 readback, normal stock return, interpretation and standing eventual manual Power fallback. Loss/torn/unjoined/ambiguous results stop as UNKNOWN. No automatic retry, new candidate, next channel, bypass, charging/thermal/fake or scheduler/clock fix; consult Large before any further guesses. No fullOS GO.
