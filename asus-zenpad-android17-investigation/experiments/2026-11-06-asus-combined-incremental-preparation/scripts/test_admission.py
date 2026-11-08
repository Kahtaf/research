from pathlib import Path
import copy
import unittest
from admission import compose, check_source_map, admit, require_binding, read
HOME = Path(__file__).resolve().parents[1]
class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.base = read(HOME / 'inputs/root-baseline-product.json')
        self.journal = read(HOME / 'inputs/profile-journal.json')
        self.expected = read(HOME / 'inputs/expected-profile-product.json')
    def test_exact_ten_source_delta(self):
        self.assertEqual(compose(self.base, self.journal), self.expected)
        check_source_map(self.expected, self.expected)
    def test_unknown_source_refused(self):
        actual = dict(self.expected, unexpected={'sha256':'unapproved'})
        with self.assertRaises(ValueError): check_source_map(actual, self.expected)
    def test_wrong_root_mk_refused(self):
        actual = dict(self.expected, **{'lineage_p00a.mk':self.base['device.mk']})
        with self.assertRaises(ValueError): check_source_map(actual, self.expected)
    def test_wrong_profile_preimage_refused(self):
        journal = copy.deepcopy(self.journal)
        journal['changes'][0]['before_sha256'] = self.base['lineage_p00a.mk']['sha256']
        with self.assertRaises(ValueError): compose(self.base, journal)
    def test_missing_namespace_refuses_admission(self):
        with self.assertRaisesRegex(ValueError, 'Namespace handoff is missing'): admit(HOME, None, None)
    def test_missing_binding_refuses_execution_before_vm_access(self):
        with self.assertRaisesRegex(ValueError, 'unbound'): require_binding(HOME)
if __name__ == '__main__': unittest.main()
