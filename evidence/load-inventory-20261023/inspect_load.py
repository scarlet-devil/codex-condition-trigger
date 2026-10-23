"""Read-only bounded inventory of the fixed Desktop installation. No target writes."""
import base64
import hashlib
import json
import struct
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(r'C:\Program Files\WindowsApps\OpenAI.Codex_26.1016.8622.0_x64__2p2nqsd0c76g0')
OUT = Path(__file__).resolve().parent
TARGETS = ('app/ChatGPT.exe', 'app/chrome.dll', 'app/resources/app.asar')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pe_resources(data):
    def unpack(fmt, pos):
        size = struct.calcsize(fmt)
        if pos < 0 or pos + size > len(data):
            raise ValueError('PE read out of bounds')
        return struct.unpack_from(fmt, data, pos)

    if data[:2] != b'MZ':
        raise ValueError('Missing DOS header')
    pe = unpack('<I', 0x3c)[0]
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Missing PE header')
    _, count, _, _, _, opt_size, _ = unpack('<HHIIIHH', pe + 4)
    opt = pe + 24
    magic = unpack('<H', opt)[0]
    dd = opt + {0x10b: 96, 0x20b: 112}[magic]
    if dd + 8 * 5 > opt + opt_size or not 1 <= count <= 96:
        raise ValueError('Invalid PE directory extent')
    resource_rva, resource_size = unpack('<II', dd + 16)
    cert_offset, cert_size = unpack('<II', dd + 32)
    sections = []
    for i in range(count):
        pos = opt + opt_size + i * 40
        vs, va, rs, rp = unpack('<IIII', pos + 8)
        sections.append((data[pos:pos+8].rstrip(b'\0').decode('ascii'), vs, va, rs, rp))

    def map_rva(rva, length):
        matched = [(n, rp+rva-va) for n, vs, va, rs, rp in sections
                   if va <= rva and rva + length <= va + rs]
        if len(matched) != 1:
            raise ValueError('Ambiguous/unmapped RVA')
        name, pos = matched[0]
        if pos + length > len(data):
            raise ValueError('RVA beyond file')
        return name, pos

    result = {'certificate_table_offset': cert_offset, 'certificate_table_bytes': cert_size,
              'resource_rva': resource_rva, 'resource_bytes': resource_size,
              'matching_resources': []}
    if not resource_rva or not resource_size:
        return result
    _, root = map_rva(resource_rva, resource_size)

    def within(rel, length):
        if rel < 0 or rel + length > resource_size:
            raise ValueError('Resource read out of bounds')
        return root + rel

    def label(raw):
        if not raw & 0x80000000:
            return raw
        rel = raw & 0x7fffffff
        length = unpack('<H', within(rel, 2))[0]
        pos = within(rel+2, length*2)
        return data[pos:pos+length*2].decode('utf-16le')

    def entries(rel):
        pos = within(rel, 16)
        named, ids = unpack('<HH', pos+12)
        total = named + ids
        if total > 4096:
            raise ValueError('Resource entry budget exceeded')
        within(rel+16, total*8)
        return [(label(n), v) for n, v in
                (unpack('<II', pos+16+i*8) for i in range(total))]

    top = entries(0)
    result['resource_types'] = [n for n, _ in top]
    for typ, branch in top:
        if not isinstance(typ, str) or typ.casefold() != 'integrity':
            continue
        if not branch & 0x80000000:
            raise ValueError('Expected resource type directory')
        for name, sub in entries(branch & 0x7fffffff):
            if not isinstance(name, str) or name.casefold() != 'electronasar':
                continue
            if not sub & 0x80000000:
                raise ValueError('Expected resource name directory')
            for language, leaf in entries(sub & 0x7fffffff):
                if leaf & 0x80000000:
                    raise ValueError('Unexpected resource depth')
                rva, length, cp, reserved = unpack('<IIII', within(leaf, 16))
                if length > 65536 or reserved:
                    raise ValueError('Invalid or oversized resource')
                section, pos = map_rva(rva, length)
                payload = data[pos:pos+length]
                decoded = json.loads(payload.decode('utf-8').rstrip('\0'))
                result['matching_resources'].append({
                    'type': typ, 'name': name, 'language': language, 'codepage': cp,
                    'file_offset': pos, 'bytes': length, 'section': section,
                    'sha256': sha(payload), 'json': decoded,
                    'outside_certificate_table': pos+length <= cert_offset or pos >= cert_offset+cert_size})
    return result


def main():
    (OUT/'private').mkdir(exist_ok=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    started = time.time()
    evidence = {'schema': 1, 'scope': list(TARGETS), 'files': {}, 'source_stable': True}
    for relative in TARGETS:
        path = ROOT / relative
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        stable = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        entry = {'bytes': len(raw), 'sha256': sha(raw), 'read_stable': stable}
        if relative.endswith('.asar'):
            magic, header_size, payload_size, json_size = struct.unpack('<4I', raw[:16])
            if magic != 4 or json_size > header_size-8 or json_size < 2:
                raise ValueError('Invalid ASAR header')
            header_raw = raw[16:16+json_size]
            json.loads(header_raw)
            entry['raw_json_header'] = {'offset': 16, 'bytes': json_size, 'sha256': sha(header_raw),
                                        'header_size_field': header_size, 'pickle_payload_size': payload_size}
            (OUT / 'private/original-asar-json-header.bin').write_bytes(header_raw)
        else:
            entry['pe'] = pe_resources(raw)
        evidence['files'][relative] = entry
        evidence['source_stable'] &= stable
        del raw
    expected = evidence['files']['app/resources/app.asar']['raw_json_header']['sha256']
    for relative in TARGETS[:2]:
        for resource in evidence['files'][relative]['pe']['matching_resources']:
            resource['entries'] = [dict(item, matches_original_raw_header=(
                item.get('file') == 'resources\\app.asar' and item.get('alg', '').lower() == 'sha256'
                and item.get('value') == expected)) for item in resource['json']]

    manifest_raw = (ROOT / 'AppxManifest.xml').read_bytes()
    manifest = ET.fromstring(manifest_raw)
    evidence['package_manifest'] = {'bytes': len(manifest_raw), 'sha256': sha(manifest_raw),
        'identity': next(e.attrib for e in manifest if e.tag.endswith('}Identity')),
        'applications': [e.attrib for e in manifest.iter() if e.tag.endswith('}Application')],
        'dependencies': [e.attrib for e in manifest.iter() if e.tag.endswith('}TargetDeviceFamily')]}
    map_raw = (ROOT / 'AppxBlockMap.xml').read_bytes()
    blockmap = ET.fromstring(map_raw)
    evidence['blockmap'] = {'bytes': len(map_raw), 'sha256': sha(map_raw),
                           'hash_method': blockmap.attrib['HashMethod'], 'files': {}}
    if not blockmap.attrib['HashMethod'].endswith('#sha256'):
        raise ValueError('Unsupported block hash algorithm')
    for elem in blockmap:
        name = elem.attrib.get('Name', '').replace('\\', '/')
        if name not in TARGETS:
            continue
        blocks = [e for e in elem if e.tag == '{http://schemas.microsoft.com/appx/2010/blockmap}Block']
        file_hashes = [e for e in elem if e.tag == '{http://schemas.microsoft.com/appx/2021/blockmap}FileHash']
        matches = 0
        with (ROOT/name).open('rb') as stream:
            for block in blocks:
                chunk = stream.read(65536)
                matches += base64.b64encode(hashlib.sha256(chunk).digest()).decode() == block.attrib['Hash']
            extra = stream.read(1)
        evidence['blockmap']['files'][name] = {
            'declared_bytes': int(elem.attrib['Size']), 'blocks': len(blocks), 'matching_blocks': matches,
            'file_hash_count': len(file_hashes),
            'file_hash_match': len(file_hashes) == 1 and base64.b64decode(file_hashes[0].attrib['Hash']).hex() == evidence['files'][name]['sha256'],
            'all_match': matches == len(blocks) and not extra
            and int(elem.attrib['Size']) == evidence['files'][name]['bytes']}
    signature = (ROOT / 'AppxSignature.p7x').read_bytes()
    evidence['package_signature_file'] = {'bytes': len(signature), 'sha256': sha(signature),
                                         'magic_hex': signature[:4].hex()}
    evidence['elapsed_seconds'] = round(time.time()-started, 3)
    (OUT/'evidence/static-inventory.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
