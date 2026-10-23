"""Bounded local metadata selection; no model sends or runtime-state inference."""
import json
import ntpath
import re

MAX_RECORDS = 500
MAX_METADATA_BYTES = 1024 * 1024


def normalize_local_path(value):
    if not isinstance(value, str) or not value or len(value) > 32767 or '\0' in value:
        raise ValueError('invalid_local_path')
    extended = value.startswith('\\\\?\\')
    if extended:
        value = value[4:]
        if '/' in value or any(p in ('.', '..') for p in value.split('\\')):
            raise ValueError('unsupported_extended_path_component')
    else:
        value = value.replace('/', '\\')
    if not re.match(r'^[A-Za-z]:\\', value):
        raise ValueError('unsupported_local_path')
    if any(p.endswith((' ', '.')) for p in value[3:].split('\\') if p not in ('.', '..')):
        raise ValueError('ambiguous_path_component')
    return ntpath.normcase(ntpath.normpath(value))


def select_candidates(rows, project_cwd, child_ids=()):
    if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
        raise ValueError('catalog_record_limit')
    if len(json.dumps(rows, ensure_ascii=False).encode('utf-8')) > MAX_METADATA_BYTES:
        raise ValueError('catalog_metadata_limit')
    project = normalize_local_path(project_cwd)
    children, seen, selected = set(child_ids), set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError('malformed_catalog_record')
        identity = row.get('id')
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('invalid_or_duplicate_id')
        seen.add(identity)
        if (row.get('archived') != 0
                or row.get('thread_source') not in ('user', 'agent_created_thread')
                or row.get('source') not in ('vscode', 'cli')
                or row.get('agent_path') not in (None, '', '/root')
                or identity in children):
            continue
        try:
            if normalize_local_path(row.get('cwd')) != project:
                continue
        except ValueError:
            continue
        name, title = row.get('name'), row.get('title')
        if name is not None and not isinstance(name, str):
            raise ValueError('malformed_display_name')
        if not isinstance(title, str):
            raise TypeError('malformed_title')
        display = name.strip() if name and name.strip() else title.strip()
        selected.append(dict(row, display_name=display or '(untitled)',
                             selection_key=identity, connection_status='not_queried'))
    return selected
