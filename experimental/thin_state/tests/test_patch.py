import unittest

from patch_copy import MAIN, apply_copy, revert_copy


class PatchGuardTests(unittest.TestCase):
    def test_wrong_original_bytes_refused(self):
        with self.assertRaises(ValueError):
            apply_copy(MAIN, b'unreviewed version')

    def test_unknown_module_refused(self):
        with self.assertRaises(ValueError):
            apply_copy('other.js', b'anything')

    def test_wrong_rollback_refused(self):
        with self.assertRaises(ValueError):
            revert_copy(MAIN, b'unreviewed candidate')
