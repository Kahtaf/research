from pathlib import Path
import hashlib
import json
import re

R = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda name: json.loads((R / name).read_text())
initial = read('evidence/acquire_initial.json')
binding = read('evidence/acquire_binding.json')
final = read('evidence/acquire_final.json')
handoff = read('evidence/owned-handoff.json')
prior = read('evidence/prior-SOURCE-PINS.json')
after = read('evidence/after.stdout')
assert after['id'] == '8549823276971553556'
assert after['status'] == 'TERMINATED'
assert not Path('/tmp/aspmic-e7acab50').exists()

limits = [
    'Published vmlinux SHA is reused from owned build/handoff. No fresh remote vmlinux hash or full vmlinux/out fetch. Current size, genuine System.map hash, named paths, object/cmd metadata and focused native disassembly support controlled provenance, not unconditional historical byte attestation.',
    'Owned independent-copy receipt says command/dependency paths were relocated. Current .cmd files name source inputs but do not attest immutable historical source bytes; metadata alone is not byte attestation.',
    'Config, preserved DT and linked init select the ARM virtual-counter route. Runtime registration success, live reader pointer, suspended state and selected erratum workaround were not directly observed.',
    'Only scoped clocksource registration-line search selected additional backend files. No whole-kernel audit or further power-stack acquisition.',
    'Loop bounds assume each MMIO/counter operation returns and locks are acquired. They do not bound stalled MMIO, a stalled reader, lock acquisition or scheduler waits.',
    'Physical facts supplied by parent were not decoded here. Parser framing refusal/raw artifacts remain parent-owned. WRET precedes C return and does not prove userspace resumption. Absence and cached PC are not fault evidence.'
]

sources = []
for path in sorted((R / 'source').rglob('*')):
    if not path.is_file():
        continue
    relative = str(path.relative_to(R / 'source'))
    production = relative.removeprefix('prior-hash-bound/')
    data = path.read_bytes()
    entry = dict(path=str(path.relative_to(R)), production_path=production,
                 bytes=len(data), sha256=sha(data), slices=[])
    entry['acquisition'] = ('remote hash only; copied matching preexisting local bytes'
                            if relative.startswith('prior-hash-bound/')
                            else 'current named remote kernel source bytes')
    if production in initial['hashes']:
        entry['remote_metadata'] = initial['hashes'][production]
    entry['prior_local_pins'] = [
        dict(path=e['path'], sha256=e['sha256'], matches=e['sha256'] == sha(data))
        for e in prior['source_entries'] if e['path'].endswith('/' + production)
    ]
    for sliced in sorted((R / 'slices' / relative).glob('*.txt')):
        match = re.fullmatch(r'(\d+)-(\d+)\.txt', sliced.name)
        first, last = map(int, match.groups())
        raw = sliced.read_bytes()
        assert raw == b''.join(data.splitlines(keepends=True)[first - 1:last])
        entry['slices'].append(dict(first=first, last=last,
                                    path=str(sliced.relative_to(R)), sha256=sha(raw)))
    sources.append(entry)

route = dict(
    identity=dict(kernel_uuid=handoff['identity']['kernel_uuid'],
                  fullp10=handoff['artifacts']['candidate.p10.raw'],
                  remote_root=handoff['identity']['remote_root']),
    config=dict(sha256=initial['metadata']['out/.config']['sha256'],
                PREEMPT=True, PREEMPT_COUNT=True, PREEMPT_RCU=True, HZ=250,
                MTK_PMIC_WRAP=True, MTK_PMIC_WRAP_HAL=False, MFD_MT6397=True,
                ASUS_P00A_BATTERY_DIAGNOSTIC=True, MTK_AUXADC=False,
                ARM_ARCH_TIMER=True, GENERIC_SCHED_CLOCK=True, ACPI=False),
    dt=dict(runtime_sha256=handoff['artifacts']['runtime.dtb']['sha256'],
            compiled_sha256=sha((R / 'evidence/compiled.dtb').read_bytes()),
            remote_compiled=final['details']['arch/arm64/boot/dts/mediatek/asus-p00a.dtb'],
            selected_properties='evidence/dt-route.json',
            wrapper='/soc/pwrap@0x1000d000',
            compatible=['mediatek,mt8163-pwrap', 'mediatek,mt6323', 'mediatek,mt6323-pmic'],
            timer='/timer', timer_compatible='arm,armv8-timer', timer_dt_rate_hz=13000000,
            dt_command_receipt='evidence/acquire_final.json:details.dt_cmd'),
    route=[
        'power_supply_changed_work releases changed_lock before kobject uevent',
        'power_supply_uevent iterates finite property list; property callback is battery_get_property',
        'battery_get_property dispatches diagnostic callback; voltage asks AUXADC channel6, five samples',
        'pwrap_probe matches MT8163/MT6323, creates generic fast_io regmap and populates child',
        'mt6397_probe obtains parent dev_get_regmap; pmic_mt6323_probe stores MFD regmap in pwrap_regmap',
        'pmic read/config interfaces use regmap_read/write; nolock omits only pmic_access_mutex',
        'regmap locks map spinlock IRQ-save over pwrap_regmap_read/write and releases after return'
    ],
    native_regmap_configuration=read('evidence/decoded-regmap-config.json'),
    lock_nesting=dict(
        preparation=['wake source', 'pmic_adc_mutex', 'pmic_adc_lock IRQ-save', 'regmap spinlock IRQ-save', 'pwrap poll'],
        samples=['wake source', 'pmic_adc_mutex', 'pmic_access_mutex', 'regmap spinlock IRQ-save', 'pwrap poll'],
        delay='ADC mutex held; no ADC spinlock or regmap lock surrounds udelay(300)',
        ELF='regmap_lock_spinlock calls _raw_spin_lock_irqsave; native code masks IRQ and increments preempt count'),
    clock=dict(
        registration='arch_timer_common_init inlines arch_counter_register: sched_clock_register(arch_timer_read_counter,56,arch_timer_rate)',
        selected_reader='arch_counter_get_cntvct', reader_address='0xffffff800886f5a0',
        instruction='ISB then CNTVCT_EL0 MRS, or configured out-of-line counter workaround',
        width_bits=56, rate_hz=13000000,
        rate_basis='preserved runtime/compiled DT clock-frequency; arch_timer_detect_rate DT branch, ACPI absent',
        optional_readers=[
            dict(name='arm64_1188873_read_cntvct_el0', bound='one CNTVCT_EL0 MRS'),
            dict(name='fsl_a008585_read_cntvct_el0', bound='200 pairs maximum; WARN_ON_ONCE exhaustion')],
        jiffies='generic initialization/fallback only; not selected ARM hardware reader',
        sequence='two-copy latch; linked read chooses seq&1, retries changed sequence, does not wait for odd writer',
        hrtimer='epoch/wrap refresh; direct counter delta advances between refreshes without delivered IRQ',
        suspend='syscore suspend intentionally replaces reader with frozen epoch; no evidence of this in suspect path'),
    waits=[
        dict(name='pwrap_read', source='drivers/soc/mediatek/mtk-pmic-wrap.c:676-751',
             bound='FSM_IDLE and WFVLDCLR each elapsed sched_clock 10000000ns, final readiness recheck; no iteration bound',
             error='-ETIMEDOUT; idle failure checks/clears VLDCLR; post-command timeout returns without immediate clear'),
        dict(name='pwrap_write', source='drivers/soc/mediatek/mtk-pmic-wrap.c:715-728',
             bound='one identical idle poll, then issues command; no synchronous write-completion poll',
             error='idle recovery and -ETIMEDOUT'),
        dict(name='pwrap_timeout_ns regression branch', source='drivers/soc/mediatek/mtk-pmic-wrap.c:676-695',
             bound='cur<start replaces helper-local start only; repeated values below caller start yield elapsed zero'),
        dict(name='ADC prepare', source='pmic_battery.inc:22-69; pmic_mt6323.c:68',
             bound='100 iterations; restore ADC IRQ-save lock before usleep_range(1000,2000)',
             error='propagate inner errors or -ETIMEDOUT; inner transport must return first'),
        dict(name='ADC sampling', source='pmic_battery.inc:149-218; battery_diag.c:68-90',
             bound='five channel6 samples; udelay(300); each at most100 readiness reads with usleep_range(1000,2000)',
             error='inner errors/-ETIMEDOUT release ADC mutex and wake source; property error propagated; uevent skips ENODATA/ENODEV only'),
        dict(name='original virtual delay', source='arch/arm64/lib/delay.c:28-92',
             bound='64-bit cycles elapsed; get_cycles compiled as CNTVCT, optional OOL reader; no iteration bound',
             error='void return; LPJ*HZ scales requested cycles, no elapsed jiffies dependency; transport fallback does not cure stalled delay'),
        dict(name='legacy PMIC_IMM_PollingAuxadcChannel', source='pmic_mt6323.c:265-318',
             bound='unbounded legacy poll; channel4-7 delegation bypasses it on checked channel6 path')],
    answer=dict(IRQ_off_preemption_off_polling=True, independent_iteration_fallback=False,
                self_blocking_jiffies_or_IRQ_dependency_established=False,
                risk='conditional nonprogress only; latent risk remains, physical root cause unproved',
                qualification='Once lock acquired and assuming all MMIO/counter operations return, hardware readiness or elapsed sched_clock are the pwrap poll exits'),
    review_only_fallback=dict(
        location='pwrap_wait_for_state',
        logic='Preserve existing readiness/deadline semantics; add independently decrementing finite poll budget. At deadline or budget exhaustion recheck readiness once, return 0 or -ETIMEDOUT through existing cleanup. Each poll consumes budget even for equal or backward clock values.',
        budget='Unspecified. Derive a defensible budget from hardware transaction timing and supported execution-speed envelope before review; iterations are not walltime.',
        risks=['false timeout on slow valid transactions', 'pending command/recovery and next transaction synchronization', 'applies to shared initialization and other PMIC consumers', 'stalled MMIO/reader or lock cannot be bounded by outer budget', 'void __delay must not silently under-delay']),
    limits=limits)
(R / 'ACTUAL-ROUTE.json').write_text(json.dumps(route, indent=2) + '\n')

pins = dict(
    date='2026-11-08', status='ONE_BOUNDED_UNIT_COMPLETE_STOP',
    scope=dict(remotely_fetched_production_bodies=8, initial_gap_C_files=5,
               additional_backend_C_files=1, additional_backend_headers=1, additional_DT_source_files=1,
               existing_five_S_and_original_delay_remote_hash_only=6,
               no_build_compile_test_candidate_trial=True),
    identity=dict(kernel_uuid=handoff['identity']['kernel_uuid'],
                  fullp10=handoff['artifacts']['candidate.p10.raw'],
                  vmlinux_published=handoff['remote_vmlinux'],
                  current_metadata=initial['metadata']),
    sources=sources, actual_route='ACTUAL-ROUTE.json',
    ELF_symbols=binding['disassembled'], additional_ELF=final['details'],
    VM=dict(id=after['id'], status=after['status'], owned_master_closed=True,
            channel='/tmp/aspmic-e7acab50', TCP_fallback=False), limits=limits)
(R / 'SOURCE-PINS.json').write_text(json.dumps(pins, indent=2) + '\n')

manifest = {}
for path in sorted(R.rglob('*')):
    if path.is_file() and path.name != 'ARTIFACT-MANIFEST.json':
        data = path.read_bytes()
        manifest[str(path.relative_to(R))] = dict(bytes=len(data), sha256=sha(data))
(R / 'ARTIFACT-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(dict(status=pins['status'], sources=len(sources), artifacts=len(manifest), VM=after['status'])))
