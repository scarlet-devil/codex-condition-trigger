"""Pure bytes transform for three exact reviewed modules, never an installer."""
import hashlib
from pathlib import Path

MAIN = '.vite/build/src-CsH31EEu.js'
VIEW = 'webview/assets/app-initial-ad16eaadf81f.js'
WIRE = '.vite/build/application-network-startup-BG13czUt.js'
INPUTS = {
    MAIN: '6a266611954c6f0c72aca09bb13c0c793959a69e8d6330778a7cdef21835a1db',
    VIEW: '84d1c97245fec7be606fd1d263459d9a4c841836751c6ba5e9b348b69687332f',
    WIRE: '90db83017c05bf247b53a09bb04a3312e0003259c56144535b09805085b16a6c',
}
CASE = b'case`thread-follower-read-model-settings`:{'
NEW_CASE = (b'case`thread-follower-read-thread-status`:return{method:t.method,'
            b'result:await kelanThinFollower(e,t.params)};' + CASE)
EDITS = {
    MAIN: [
        (b'"thread-follower-read-model-settings":1,',
         b'"thread-follower-read-model-settings":1,"thread-follower-read-thread-status":1,'),
        (b'o(`thread-follower-read-model-settings`),',
         b'o(`thread-follower-read-model-settings`),o(`thread-follower-read-thread-status`),'),
        (CASE, NEW_CASE),
        (b'this.handleClientRequest=r.handleClientRequest,this.handleHostRequest=r.handleHostRequest,',
         b'[this.handleClientRequest,this.handleHostRequest]=kelanThinHandlers(this,r.handleClientRequest,r.handleHostRequest),'),
    ],
    VIEW: [(CASE, NEW_CASE)],
    WIRE: [(b'function Wc(e){return Uc(JSON.stringify(e))}',
            (b'function Wc(e){let t=JSON.stringify(e);if(e.type===`response`&&'
            b'e.method===`thread-follower-read-thread-status`&&Buffer.byteLength(t,`utf8`)>65536)'
            b'throw Error(`thin-state-response-oversize`);return Uc(t)}'))],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def helper_bytes():
    source = (Path(__file__).parent / 'thin_bridge.js').read_bytes()
    marker = b'// EXPORTS_START'
    if source.count(marker) != 1:
        raise ValueError('helper marker mismatch')
    return b'\n/* KELAN_THIN_STATE_COPY_CANDIDATE_V1 */\n' + source.split(marker)[0] + b'\n'


def apply_copy(name, original):
    if name not in INPUTS or sha(original) != INPUTS[name]:
        raise ValueError('unsupported source hash/version')
    result = original
    for old, new in EDITS[name]:
        if result.count(old) != 1 or new in result:
            raise ValueError('ambiguous patch anchor')
        result = result.replace(old, new, 1)
    return result + (b'' if name == WIRE else helper_bytes())


def revert_copy(name, patched):
    if name not in INPUTS or (name != WIRE and not patched.endswith(helper_bytes())):
        raise ValueError('unsupported candidate')
    restored = patched if name == WIRE else patched[:-len(helper_bytes())]
    for old, new in reversed(EDITS[name]):
        if restored.count(new) != 1:
            raise ValueError('ambiguous rollback anchor')
        restored = restored.replace(new, old, 1)
    if sha(restored) != INPUTS[name]:
        raise ValueError('rollback hash mismatch')
    if apply_copy(name, restored) != patched:
        raise ValueError('unreviewed extra changes')
    return restored
