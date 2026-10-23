import unittest

from experimental import conversation_catalog as cat


def row(identity='one', **values):
    data={'id': identity, 'name': '', 'title': 'same', 'cwd': r'D:\project', 'archived': 0,
          'source': 'vscode', 'thread_source': 'user', 'agent_path': None,
          'rollout_path': r'D:\codex\sessions\one.jsonl', 'updated_at': 1, 'has_user_event': 0}
    data.update(values)
    return data


class CatalogTests(unittest.TestCase):
    def test_native_user_authorized_created_chat_is_candidate(self):
        rows = [row('new', thread_source='agent_created_thread')]
        self.assertEqual([r['id'] for r in cat.select_candidates(rows, r'D:\project')], ['new'])
        self.assertEqual(cat.select_candidates(rows, r'D:\project', {'new'}), [])

    def test_extended_local_drive_equivalent(self):
        self.assertEqual(cat.normalize_local_path(r'\\?\D:\Project'),r'd:\project')

    def test_extended_dot_segments_and_slash_are_not_canonicalized(self):
        for path in [r'\\?\D:\elsewhere\..\project', r'\\?\D:\project\.', r'\\?\D:/project']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                cat.normalize_local_path(path)
            self.assertEqual(cat.select_candidates([row(cwd=path)], r'D:\project'), [])

    def test_trailing_dot_or_space_components_rejected(self):
        for path in [r'D:\project.', 'D:\\project ', r'\\?\D:\project.', '\\\\?\\D:\\project ']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                cat.normalize_local_path(path)

    def test_nonlocal_device_and_relative_paths_rejected(self):
        for path in [r'\\?\UNC\host\share',r'\\.\pipe\name',r'\\?\Volume{abc}\x',
                     r'\\server\share',r'D:relative','relative','/home/me']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                cat.normalize_local_path(path)

    def test_only_user_top_level_nonarchived_candidates(self):
        rows=[row(),row('arch',archived=1),row('child',thread_source='subagent'),
              row('guard',thread_source='guardian_review'),row('unknown',thread_source=None),
              row('nested',agent_path='/root/worker'),row('source',source='{"subagent":{}}')]
        self.assertEqual([r['id'] for r in cat.select_candidates(rows,r'D:\project')],['one'])

    def test_spawn_relation_overrides_user_metadata(self):
        self.assertEqual(cat.select_candidates([row()],r'D:\project',{'one'}),[])

    def test_display_name_priority_and_duplicate_ids_preserved(self):
        rows=[row('a',name='renamed'),row('b',title='renamed')]
        result=cat.select_candidates(rows,r'D:\project')
        self.assertEqual([r['display_name'] for r in result],['renamed','renamed'])
        self.assertEqual({r['id'] for r in result},{'a','b'})
        self.assertEqual(len({r['selection_key'] for r in result}),2)

    def test_user_event_false_is_not_hidden(self):
        self.assertEqual(len(cat.select_candidates([row(has_user_event=0)],r'D:\project')),1)

    def test_wrong_project_and_unsupported_path_excluded(self):
        self.assertEqual(cat.select_candidates([row(cwd=r'E:\other'),row('dev',cwd=r'\\?\Volume{x}\p')],r'D:\project'),[])

    def test_duplicate_id_fails_closed(self):
        with self.assertRaises(ValueError):
            cat.select_candidates([row(),row()],r'D:\project')

    def test_metadata_budget_and_malformed_record(self):
        with self.assertRaises(ValueError):
            cat.select_candidates([row(str(i)) for i in range(501)],r'D:\project')
        with self.assertRaises(ValueError):
            cat.select_candidates([row(title='x'*(1024*1024+1))],r'D:\project')

if __name__=='__main__':
    unittest.main()
