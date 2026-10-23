"""Cross-check static PE parsing through Windows data-only resource mapping."""
import ctypes as C
import hashlib
import json
from pathlib import Path

ROOT = Path(r'C:\Program Files\WindowsApps\OpenAI.Codex_26.1016.8622.0_x64__2p2nqsd0c76g0\app')
OUT = Path(__file__).resolve().parent
k = C.WinDLL('kernel32', use_last_error=True)
k.LoadLibraryExW.argtypes = [C.c_wchar_p, C.c_void_p, C.c_uint32]
k.LoadLibraryExW.restype = C.c_void_p
k.FindResourceExW.argtypes = [C.c_void_p, C.c_wchar_p, C.c_wchar_p, C.c_ushort]
k.FindResourceExW.restype = C.c_void_p
k.SizeofResource.argtypes = [C.c_void_p, C.c_void_p]
k.SizeofResource.restype = C.c_uint32
k.LoadResource.argtypes = [C.c_void_p, C.c_void_p]
k.LoadResource.restype = C.c_void_p
k.LockResource.argtypes = [C.c_void_p]
k.LockResource.restype = C.c_void_p
k.FreeLibrary.argtypes = [C.c_void_p]
k.FreeLibrary.restype = C.c_int
baseline = json.loads((OUT/'evidence/static-inventory.json').read_bytes())
results = []
for filename in ('ChatGPT.exe', 'chrome.dll'):
    module = k.LoadLibraryExW(str(ROOT/filename), None, 0x40 | 0x20)
    if not module:
        raise C.WinError(C.get_last_error())
    try:
        resource = k.FindResourceExW(module, 'INTEGRITY', 'ELECTRONASAR', 1033)
        expected = baseline['files']['app/'+filename]['pe']['matching_resources']
        row = {'file': filename, 'flags': 'LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE | LOAD_LIBRARY_AS_IMAGE_RESOURCE'}
        if resource:
            size = k.SizeofResource(module, resource)
            if not 0 < size <= 65536:
                raise ValueError('Resource size outside scope')
            handle = k.LoadResource(module, resource)
            if not handle:
                raise C.WinError(C.get_last_error())
            address = k.LockResource(handle)
            if not address:
                raise C.WinError(C.get_last_error())
            raw = C.string_at(address, size)
            row.update(bytes=size, sha256=hashlib.sha256(raw).hexdigest(), json=json.loads(raw))
            row['matches_static_parser'] = len(expected) == 1 and row['sha256'] == expected[0]['sha256']
        else:
            row['win32_error'] = C.get_last_error()
            row['matches_static_parser'] = not expected and row['win32_error'] == 1813
        assert row['matches_static_parser'], row
        results.append(row)
    finally:
        if not k.FreeLibrary(module):
            raise C.WinError(C.get_last_error())
result = {'crosschecks': results, 'executable_entrypoints_invoked': False, 'all_match': True}
(OUT/'evidence/resource-crosscheck.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
