"""Exact already-integrated r3 continuation; the sole source write is BoardConfig."""
import datetime
import os
from pathlib import Path
import re
import shutil

R3_SEAL = 'a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c'
PRE = '0e012287927a5b8ac3733f7fcc28d5cdc0eb1d8f06e82e0ff6ad211fe2f72f90'
POST = '9207c304761cf86afb423641534ed383e7f8dae613e64061e972d2f65832aa4d'
LOG = 'ee061d878227210f7c2330bb36ca13f76a9daa37e354a178d733327695cfd4e0'

def sensor_delta(plan):
    from integrate import read, need, sha
    d = read(plan['sensor_delta'])
    need(d == dict(relative='sensors/BoardConfig.mk', before=PRE, after=POST,
                   old_line='P00A_ACCEL_BOARD_PATH := $(call my-dir)\n',
                   new_line='P00A_ACCEL_BOARD_PATH := device/asus/p00a/sensors\n'), 'Sensor delta selection changed')
    before = Path(plan['sensor_origin']) / 'BoardConfig.mk'
    after = Path(plan['sensor_postimage'])
    need(sha(before) == PRE and sha(after) == POST, 'Sensor delta pin mismatch')
    need(before.read_bytes().count(d['old_line'].encode()) == 1 and
         before.read_bytes().replace(d['old_line'].encode(), d['new_line'].encode()) == after.read_bytes(),
         'Sensor delta must be the exact one-line replacement')
    return d

def continuation_inputs(plan):
    from integrate import need, read, sha, verify_pins, manifest
    d = sensor_delta(plan)
    prior = Path(plan['prior_kit'])
    need(plan['prior_kit_seal'] == R3_SEAL == sha(prior / 'inputs/kit-pins.json'), 'r3 ancestor seal changed')
    need(verify_pins(prior) == R3_SEAL, 'r3 ancestor file drift')
    pins = read(plan['prior_pins'])
    actual_attempt = manifest(plan['prior_attempt'])
    expected_attempt = {str(Path(k).relative_to(plan['prior_attempt'])): {'sha256': v['sha256']}
                        for k, v in pins['attempt_files'].items()}
    need(actual_attempt == expected_attempt, 'Preserved r3 attempt changed')
    for path, row in pins['logs'].items():
        need(sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes'], 'Prior r5/r6 evidence changed: ' + path)
    actual_logs = {str(p) for rev in ('r5', 'r6') for p in Path(plan['logs']).glob('full-build-' + rev + '.*')}
    need(actual_logs == set(pins['logs']), 'Prior r5/r6 evidence file set changed')
    old = read(plan['prior_staged_receipt']); new = read(plan['staged_receipt'])
    expected = read(plan['prior_staged_receipt'])
    need(expected['product_after'][d['relative']] == {'sha256': PRE}, 'r3 sensor preimage changed')
    expected['product_after'][d['relative']] = {'sha256': POST}
    need(new == expected, 'r7 staged receipt contains unrelated changes')
    old_sensor = read(plan['prior_sensor_receipt']); new_sensor = read(plan['sensor_receipt'])
    old_sensor['files']['BoardConfig.mk'] = {'sha256': POST}
    old_sensor['board_path_adjustment'] = 'One exact reviewed assignment replaces unavailable my-dir; policy and manifest unchanged'
    need(new_sensor == old_sensor, 'r7 sensor receipt contains unrelated changes')
    stage_manifest = read(plan['staging_manifest'])
    need(manifest(plan['staging']) == stage_manifest, 'r7 staging file set or bytes changed')
    original_manifest = read(Path(plan['run_root']) / 'inputs/r3-staging-manifest.json')
    need(manifest('/srv/android/asus-product-integration-staging/r3') == original_manifest, 'r3 staging drift')
    expected_stage = dict(original_manifest)
    for name in ('STAGED.json','sensor-selection.json'):
        expected_stage[name] = {'sha256': sha(plan['staged_receipt'] if name == 'STAGED.json' else plan['sensor_receipt'])}
    expected_stage['product-device/' + d['relative']] = {'sha256': POST}
    need(stage_manifest == expected_stage, 'r7 staging includes unrelated delta')
    integration = read(plan['prior_integration'])
    need(integration == read(prior / 'attempt/integration.json'), 'Prior integration receipt mismatch')
    need(integration['product_after'] == old['product_after'] and
         integration['staged_receipt_sha256'] == sha(plan['prior_staged_receipt']) and
         integration['sensor_receipt_sha256'] == sha(plan['prior_sensor_receipt']), 'Prior r3 integration provenance mismatch')
    for key, path in [('source_patch_sha256','patch'),('source_receipt_sha256','source_receipt'),('parent_parity_receipt_sha256','parity_receipt')]:
        need(integration[key] == sha(plan[path]), 'Inherited integration provenance changed: ' + key)
    need(integration['kernel_sha256'] == old['product_after']['prebuilt/Image.gz-dtb']['sha256'] and
         integration['generated_defconfig']['sha256'] == old['kernel_config_sha256'], 'Inherited physical kernel/config changed')
    need(integration['flash_ready'] is False, 'Unexpected physical acceptance')
    return d

def terminal(plan, review=None, describe=False):
    from integrate import need, sha, read
    prefix = Path(plan['logs']) / 'full-build-r6'
    paths = {n: Path(str(prefix) + '.' + n) for n in ('started','finished','exit-code','log')}
    need(all(p.is_file() and not p.is_symlink() and p.stat().st_size for p in paths.values()), 'r6 is not an actual terminal result')
    need(paths['exit-code'].read_text().strip() == '1', 'Unexpected r6 exit; exact failure review required')
    start = datetime.datetime.fromisoformat(paths['started'].read_text().strip())
    end = datetime.datetime.fromisoformat(paths['finished'].read_text().strip())
    need(start.tzinfo and end.tzinfo and start <= end <= datetime.datetime.now(datetime.timezone.utc), 'Incoherent r6 terminal times')
    need(end.isoformat() == '2026-11-06T22:28:00.150539+00:00', 'Unexpected r6 terminal identity')
    need(not Path(str(prefix) + '.complete').exists(), 'r6 failed result has success marker')
    failed = Path(plan['prior_attempt']) / 'FAILED.json'
    need(failed.is_file() and read(failed).get('retry_allowed') is False, 'r6 lacks preserved terminal FAILED.json')
    need(sha(paths['log']) == LOG, 'Actual r6 terminal log changed')
    pins = read(plan['prior_pins'])
    for group in ('logs','attempt_files'):
        for path, row in pins[group].items():
            need(sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes'], 'Prior preservation pin changed: ' + path)
    need({str(p) for p in Path(plan['prior_attempt']).rglob('*') if p.is_file() or p.is_symlink()} == set(pins['attempt_files']), 'Prior attempt file set changed')
    need({str(p) for r in ('r5','r6') for p in Path(plan['logs']).glob('full-build-' + r + '.*')} == set(pins['logs']), 'Prior evidence file set changed')
    observed = dict(revision='r6', exit_code=1, terminal_kind='ACTUAL_BUILD_FAILURE',
                    terminal_log_sha256=LOG, r3_kit_pins_sha256=R3_SEAL,
                    preservation=pins, images={p.name: {'sha256':sha(p),'bytes':p.stat().st_size}
                    for p in sorted(Path(plan['product_out']).glob('*.img'))})
    template = dict(reviewed_by_parent=False, reason='', prior=observed)
    if describe:
        return dict(status='TERMINAL_FAILED_REQUIRES_PARENT_REVIEW', review_template=template)
    need(review is not None, 'Prior r6 actually failed: explicit hash-bound parent failure acceptance required')
    path, digest = review
    need(Path(path).resolve().is_relative_to(Path(plan['run_root']) / 'parent-review'), 'Failure acceptance must be in own parent-review directory')
    need(re.fullmatch('[0-9a-f]{64}', digest or '') and not Path(path).is_symlink() and sha(path) == digest, 'Parent failure acceptance pin mismatch')
    accepted = read(path)
    need(set(accepted) == {'reviewed_by_parent','reason','prior'} and accepted['reviewed_by_parent'] is True and
         isinstance(accepted['reason'], str) and bool(accepted['reason'].strip()), 'r6 failure not explicitly accepted by parent')
    need(accepted['prior'] == observed, 'Actual r6 failure changed since parent acceptance')
    return dict(terminal_kind='FAILED_REVIEWED_FOR_NEW_REVISION', observed=observed, parent_review_sha256=digest)

def preserve(plan, attempt, previous):
    from integrate import need, read, write, item, sha, safe
    before = attempt / 'before'; before.mkdir()
    d = sensor_delta(plan)
    src = safe(plan['device'],d['relative']); dst = before / 'sensor-BoardConfig.mk'
    need(item(src) == {'sha256':PRE}, 'Sensor preimage changed before preservation')
    shutil.copy2(src,dst)
    need(item(dst) == item(src), 'Sensor preservation failed')
    logs = before / 'logs'; logs.mkdir()
    for name, row in read(plan['prior_pins'])['logs'].items():
        source = Path(name); destination = logs / source.name
        shutil.copy2(source,destination)
        need(sha(destination) == row['sha256'], 'Prior log preservation failed')
    # Never rename/remove existing product images or touch incremental cache.
    write(attempt / 'preservation.json', dict(sensor_preimage=dict(path=str(src),backup=str(dst),sha256=PRE),
          r6_failure=previous, prior_attempt_preserved_in_place=plan['prior_attempt'],
          prior_preservation_pins_sha256=sha(plan['prior_pins']),cache_preserved_in_place=True))

def apply(plan, attempt):
    from integrate import need, read, write, sha, manifest, safe, copy_exact, verify_integrated
    d = sensor_delta(plan)
    need(manifest(plan['device']) == read(plan['prior_staged_receipt'])['product_after'], 'r3 source changed before sole write')
    copy_exact(plan['sensor_postimage'], safe(plan['device'],d['relative']), {'sha256':POST})
    post = verify_integrated(plan, baseline=True)
    write(attempt / 'postimages.json', post)
    record = read(plan['prior_integration'])
    record.update(product_after=manifest(plan['device']),staged_receipt_sha256=sha(plan['staged_receipt']),
                  sensor_receipt_sha256=sha(plan['sensor_receipt']),
                  prior_integration_receipt_sha256=sha(plan['prior_integration']),sensor_delta_sha256=sha(plan['sensor_delta']),
                  source_writes=[dict(path=str(safe(plan['device'],d['relative'])),before=PRE,after=POST)],
                  preservation_receipt_sha256=sha(attempt/'preservation.json'),
                  active_source_postimages_sha256=sha(attempt/'postimages.json'),prior_kit_pins_sha256=R3_SEAL,revision='r7')
    write(attempt/'integration.json',record)
