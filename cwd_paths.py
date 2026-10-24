"""Restricted lexical cwd comparison; never resolves filesystem identities.

Windows support is limited to ordinary absolute drive paths and clean extended
drive paths. Keep namespaces, device aliases and ambiguous spellings out of the
comparison rather than deleting arbitrary prefixes or resolving links.
"""
import ntpath
import os
import re

_RESERVED = frozenset(('CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$')) | {
    prefix + digit for prefix in ('COM', 'LPT') for digit in '123456789¹²³'
}


def normalize_windows_cwd(value):
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
    parts = value[3:].split('\\')
    if extended and any(not p for p in parts[:-1]):
        raise ValueError('unsupported_extended_path_component')
    for part in parts:
        if not part or part in ('.', '..'):
            continue
        if part.endswith((' ', '.')):
            raise ValueError('ambiguous_path_component')
        if any(ord(c) < 32 or c in '<>:"|?*' for c in part):
            raise ValueError('unsupported_path_component')
        if part.split('.', 1)[0].rstrip(' ').upper() in _RESERVED:
            raise ValueError('unsupported_device_component')
    return ntpath.normcase(ntpath.normpath(value))


def cwd_matches(left, right):
    """Use the host's path rules; unsupported Windows forms never match.

    Non-Windows fixtures retain the existing case-sensitive host normalization.
    This does not claim same-file identity, link resolution or support for
    Windows directories configured with case-sensitive naming.
    """
    if not isinstance(left, str) or not isinstance(right, str) or not left or not right:
        return False
    if os.name == 'nt':
        try:
            return normalize_windows_cwd(left) == normalize_windows_cwd(right)
        except ValueError:
            return False
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(os.path.normpath(right))
