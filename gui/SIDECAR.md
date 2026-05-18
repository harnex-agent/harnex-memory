# Production sidecar plan

The first GUI slice uses the development bridge in `src-tauri/src/harnex_memory.rs`:

```text
python3 -m harnex_memory.cli ...
PYTHONPATH=<repo>/src
```

Production packaging should keep the same JSON contract and replace only the
process target:

1. Build a standalone `harnex-memory` executable from the Python package.
2. Add that executable to `src-tauri/tauri.conf.json > bundle > externalBin`.
3. Resolve the sidecar with Tauri's sidecar APIs inside the command adapter.
4. Preserve the fixed operation map:
   - `items list`
   - `items show`
   - `items preview`
   - `docs apply`
5. Keep validation and structured `BridgeError` responses in Rust.
6. Do not expose arbitrary shell execution or user-provided command arguments.

The frontend should not need contract changes when the bridge moves from
development Python execution to a packaged sidecar.
