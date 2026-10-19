# Recorded runtime source fixes

`scripts/verify_2d_parity.py` requires every file under `src/` to match the pinned upstream commit in `porting.json`, apart from the `redot-compat` selector. A fix to an upstream runtime file is allowed only when a record in this directory names it.

Each fix gets one TOML file. The file name must match its `id`:

```toml
id = "null-motion-result"
summary = "Accept a null motion result in body_test_motion instead of dereferencing it."
origin = "inherited-upstream"   # or "redot-port"
upstream = "not yet reported"   # or an upstream issue/PR link, or "fixed upstream in vX.Y.Z"
files = ["src/servers/rapier_physics_server_impl.rs"]
```

Rules enforced by the parity gate:

- Every listed file must exist in the upstream runtime source, and must actually differ from upstream. Remove a record, or a file from it, once the change is gone.
- Files that are not listed must still match upstream exactly.
- Several records may list the same file.
- The parity report lists every record, so release evidence shows exactly which upstream files carry downstream fixes.

When a fix is accepted upstream and the release line moves to that upstream version, delete its record.
