# Thin-state copy candidate

Experimental, default off. This directory contains an independent summary bridge,
a transport-injected caller and a pure byte patcher. It is not an installer,
production adapter, endpoint discovery tool or live command-line entry.

The implementation targets exactly Desktop 26.1016.8622.0 and the module hashes in
`patch_copy.INPUTS`. It does not declare other versions compatible. Keep original
full-snapshot APIs and production defaults unchanged.

## Flow

An already bound local owner receives `thread-follower-read-thread-status` v1.
The follower checks its owner lease, calls one narrow internal
`kelan/thread/read-status` method, and rechecks ownership after the response. The
native bridge requires the existing local initialized stdio connection, checks
connection object/generation/lifetime, issues one `thread/read` with
`includeTurns:false`, then returns only six scalar fields. It does not call
`ensureReady`, follow, history, resume or send a model task. Connection changes or
owner loss/reacquisition invalidate the observation.

The renderer queue can delay dispatch. A private issued/expires timestamp pair
rejects an already expired request at the native bridge; its remaining native
wait uses a monotonic deadline. Cross-process wall-clock adjustment and machine
suspend have not been tested. The external caller independently shares one
monotonic 10-second deadline from initialize through the summary response.

The caller enforces 64 KiB per frame before reading its body and 1 MiB total
receive bytes, including headers and unrelated messages. The patched wire encoder
also caps the complete new response envelope at 64 KiB. Unknown methods fail
closed, with zero retries and no full-history fallback. Idle is an observation;
the caller always returns `can_send:false`.

## Isolated tests

Use already available Python and Node runtimes; no package installation is needed
for the bridge/caller tests. From this directory:

```text
node --test tests/test_bridge.cjs
python -B -m unittest discover -s tests -p "test_*.py" -v
```

`patch_copy.apply_copy(name, bytes)` produces candidate bytes in memory.
`revert_copy` reconstructs and verifies the exact original. Neither function
opens an installation path or writes a file. Any file-writing harness must use a
dedicated copy directory. The original and patched complete vendor bundles are
private local evidence and are not included in this repository.

For someone with the exact source copies and an existing Acorn 8 installation:

```text
node tests/check_installed_copies.cjs COPY_DIRECTORY ACORN_PACKAGE_DIRECTORY
```

The copy directory contains `original__` / `patched__` plus the module path with
`/` replaced by `__`. This test parses six original/patched modules, extracts
specific real functions into synthetic VMs, and checks registration, native API
shape, protocol versions, old history behavior and framing. It never imports or
starts a complete Desktop bundle. A passing test is not a Desktop load test.

## Loading gate

The installed `chrome.dll` has both embedded ASAR integrity validation and
ASAR-only loading enabled. Its Authenticode signature was Valid during this run.
All three affected ASAR entries contain SHA256 integrity metadata. Repacking the
archive changes its header; a matching protected header baseline and a valid
installation trust plan are needed before testing that package.

This candidate does not repack ASAR, edit PE resources, change fuses, disable
integrity, re-sign binaries, install, restart, launch a copied Desktop, open IPC,
operate windows or send model requests. Those are separate decisions. A copied
Desktop with another service would not prove the original-host requirement.

The caller requires a separately verified original-host pipe. No live pipe
factory is supplied, and `enabled=True` alone is not installation verification.
The eventual verifier must bind the original signed baseline, reviewed patched
hashes, exact process/service/owner and the approved loading method. No current
production verification rule is relaxed by this package.

State: candidate code ready for review; live loading blocked pending trust-path
decision; G0 remains unaccepted; Alice review_pending.
