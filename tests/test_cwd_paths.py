"""Supported Windows spellings and rejection boundaries, using synthetic paths."""
import json
import ntpath
import posixpath
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cwd_paths as paths
import desktop_ipc as ipc
from experimental import conversation_catalog as catalog


class CwdPathTests(unittest.TestCase):
    def windows(self):
        return mock.patch.object(paths, 'os', SimpleNamespace(name='nt', path=ntpath))

    def test_supported_drive_spellings_in_both_orders(self):
        pairs = [(r'D:\Project', r'\\?\d:\project'),
                 ('D:/项目/./结果/', '\\\\?\\D:\\项目\\结果\\'),
                 (r'D:\base\child\..\project', r'\\?\D:\base\project'),
                 ('D:\\', '\\\\?\\d:\\')]
        with self.windows():
            for a, b in pairs:
                with self.subTest(a=a, b=b):
                    self.assertTrue(paths.cwd_matches(a, b))
                    self.assertTrue(paths.cwd_matches(b, a))

    def test_different_drive_or_directory_never_matches(self):
        with self.windows():
            for other in (r'E:\project', r'D:\project-other', r'D:\else\project',
                          r'\\?\D:\project\child', r'D:\PROJECT~1'):
                with self.subTest(other=other):
                    self.assertFalse(paths.cwd_matches(r'\\?\D:\project', other))

    def test_unsupported_namespaces_and_relative_paths_fail_even_when_equal(self):
        cases = [r'\\?\UNC\host\share', r'\\server\share', r'\\.\pipe\name',
                 r'\\?\Volume{abc}\project', r'\??\D:\project', r'D:project',
                 r'\project', 'project', '/project', '', None, 1, 'D:\\x\0y',
                 'D:\\' + 'x' * 32768]
        with self.windows():
            for value in cases:
                with self.subTest(value_type=type(value).__name__, length=len(value) if isinstance(value, str) else 0):
                    self.assertFalse(paths.cwd_matches(value, value))
                    with self.assertRaises(ValueError):
                        paths.normalize_windows_cwd(value)

    def test_ambiguous_extended_and_trailing_components_fail_closed(self):
        cases = [r'\\?\D:\base\..\project', r'\\?\D:\project\.', r'\\?\D:/project',
                 r'\\?\D:\\project', r'\\?\D:\project\\child', r'\\?\D:\project.',
                 '\\\\?\\D:\\project ', r'D:\project.', 'D:\\project ',
                 r'D:\bad.\project', 'D:\\bad \\project']
        with self.windows():
            for value in cases:
                with self.subTest(value=value):
                    self.assertFalse(paths.cwd_matches(value, value))
                    self.assertFalse(paths.cwd_matches(value, r'D:\project'))

    def test_device_alias_stream_and_invalid_components_are_excluded(self):
        for component in ('NUL', 'nul.txt', 'CON', 'AUX.log', 'PRN', 'COM1', 'LPT9',
                          'COM¹.txt', 'LPT²', 'CONIN$', 'CONOUT$', 'name:stream',
                          'a?b', 'a*b', 'a<b', 'a>b', 'a|b', 'a"b', 'a\nb'):
            ordinary = 'D:\\' + component + '\\project'
            extended = '\\\\?\\' + ordinary
            with self.subTest(component=component), self.windows():
                self.assertFalse(paths.cwd_matches(ordinary, extended))
                self.assertFalse(paths.cwd_matches(ordinary, ordinary))
                with self.assertRaises(ValueError):
                    paths.normalize_windows_cwd(extended)

    def test_nonwindows_host_keeps_its_existing_case_rules(self):
        with mock.patch.object(paths, 'os', SimpleNamespace(name='posix', path=posixpath)):
            self.assertTrue(paths.cwd_matches('/work', '/work/.'))
            self.assertFalse(paths.cwd_matches('/work', '/WORK'))
            self.assertFalse(paths.cwd_matches(r'D:\project', r'\\?\D:\project'))

    def test_catalog_and_runtime_use_same_supported_windows_domain(self):
        def row(identity, cwd):
            return {'id': identity, 'name': '', 'title': identity, 'cwd': cwd,
                    'archived': 0, 'source': 'vscode', 'thread_source': 'user', 'agent_path': None}
        rows = [row('ok', r'\\?\D:\project'), row('wrong', r'E:\project'),
                row('device', r'D:\NUL\..\project')]
        selected = catalog.select_candidates(rows, r'D:\project')
        self.assertEqual([r['id'] for r in selected], ['ok'])
        with self.windows():
            self.assertTrue(paths.cwd_matches(selected[0]['cwd'], r'D:\project'))

    def test_rollout_header_and_turn_context_share_drive_form_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'rollout.jsonl'
            rows = [{'type': 'session_meta', 'payload': {'id': 'target', 'cwd': r'D:\project'}},
                    {'type': 'turn_context', 'payload': {'cwd': r'\\?\D:\project'}}]
            target.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            with self.windows():
                result = ipc.rollout_state(target, 'target', r'\\?\D:\project', lifecycle=False)
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(result['settings']['cwd'], r'\\?\D:\project')
            rows[1]['payload']['cwd'] = r'E:\project'
            target.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            with self.windows(), self.assertRaises(ValueError):
                ipc.rollout_state(target, 'target', r'\\?\D:\project', lifecycle=False)


if __name__ == '__main__':
    unittest.main()
