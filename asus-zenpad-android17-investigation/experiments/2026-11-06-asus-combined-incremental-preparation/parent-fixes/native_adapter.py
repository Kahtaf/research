"""Retain exact reviewed native evidence and add the actual new image phase."""
from pathlib import Path
import importlib.util
import json

ROOT = Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1')
OWN = Path('/srv/android/asus-combined-incremental-prep-r1')
BASE = Path('/srv/android/asus-root-enabled-incremental-r1')
spec = importlib.util.spec_from_file_location('sealed_cache_lineage', ROOT / 'scripts/cache_lineage.py')
sealed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sealed)
from frozen_channel import phases, require_current_closure

class Session(sealed.Session):
    def __init__(self, root, plan, **kwargs):
        sealed.need(Path(root) == ROOT, 'Unexpected reviewed native cohort root')
        targets = set(sealed.read(plan['native_lineage_map'])['records'])
        self.retained_bundle = phases(ROOT, targets)
        self.root_enabled_bundle = phases(BASE, targets)
        sealed.need(len(self.root_enabled_bundle) == 1 and self.root_enabled_bundle[0]['receipt_sha256'] == '4f3def28f041f8bba526767b7456477a5d26b2b43316fa091a07b810a4db5c07', 'Preserved root-enabled phase pin changed')
        sealed.need(len(self.root_enabled_bundle) == 1 and self.root_enabled_bundle[0]['receipt']['exit_code'] == 0, 'Root-enabled native cohort not terminal zero')
        sealed.need(set(self.root_enabled_bundle[0]['metadata']['targets']) == {'systemimage', 'bootimage'}, 'Root-enabled selected closure changed')
        self.new_bundle = phases(OWN, targets)
        self.original_plan = sealed.read(ROOT / 'inputs/plan.json')
        super().__init__(ROOT, plan, current_bundle=self.retained_bundle + self.root_enabled_bundle + self.new_bundle, **kwargs)

    def record(self, target, source=None):
        result = super().record(target, source)
        execution = result.get('execution')
        if execution:
            phase = Path(execution['phase_path'])
            if phase.is_relative_to(OWN):
                result['actual_execution_cohort'] = 'COMBINED_INCREMENTAL'
            elif phase.is_relative_to(BASE):
                result['actual_execution_cohort'] = 'ROOT_ENABLED_INCREMENTAL'
            else:
                result['actual_execution_cohort'] = 'RETAINED_REVIEWED_R9_OR_R8'
        return result

    def final_closure(self):
        retained = require_current_closure(ROOT, self.original_plan, self.retained_bundle)
        sealed.need(len(self.new_bundle) == 1, 'Expected exactly one new native phase')
        row = self.new_bundle[0]
        import datetime
        started = datetime.datetime.fromisoformat(sealed.read(OWN / 'attempt/started.json')['utc'])
        when = datetime.datetime.fromisoformat(row['metadata']['start_time'].replace('Z', '+00:00'))
        sealed.need(row['receipt']['exit_code'] == 0 and when >= started, 'Failed or stale new native phase')
        sealed.need(len(row['metadata']['targets']) == 2 and set(row['metadata']['targets']) == {'systemimage', 'bootimage'}, 'New native selected targets differ')
        sealed.need(row['receipt']['attempt_started_sha256'] == sealed.sha(OWN / 'attempt/started.json') and
                    row['receipt']['integration_sha256'] == sealed.sha(OWN / 'attempt/integration.json'), 'New native attempt binding drift')
        return {'scope': 'CONTROLLED_RETAINED_R9_NATIVE_CLOSURE_PLUS_NEW_SELECTED_IMAGE_CLOSURE',
                'retained_native_closure': retained,
                'root_enabled_native_phase': {'path': self.root_enabled_bundle[0]['folder'], 'receipt_sha256': self.root_enabled_bundle[0]['receipt_sha256']},
                'new_image_phase': {'path': row['folder'], 'receipt_sha256': row['receipt_sha256']},
                'sole_source_delta': sealed.read(OWN / 'attempt/integration.json')['source_writes'],
                'all_61_native_rows_revalidated': True,
                'fresh_compilation_of_unchanged_native_outputs_claimed': False,
                'historical_all_input_bytes_attested': False}

def __getattr__(name):
    return getattr(sealed, name)
