# P7-G0 unchanged-source result

Status: **FAIL at compile; source remained unchanged**.

Both minimal debug profiles reached Godot Rapier Physics v0.35.2 and failed on the same first incompatible API surface:

- `single-dim2` plus `godot/api-custom-json`: generated gdext trait requires `Option<Gd<PhysicsDirectSpaceState2D>>`; upstream source selects `Gd<PhysicsDirectSpaceState2D>`.
- `single-dim3` plus `godot/api-custom-json`: generated gdext trait requires `Option<Gd<PhysicsDirectSpaceState3D>>`; upstream source selects `Gd<PhysicsDirectSpaceState3D>`.

The dependency route is verified, not inferred: the external lock resolves the complete Godot Rust family to gdext `637cef73172bba23850131acd8583b0c72ebf0c7` / 0.5.5, and retained Cargo fingerprints contain `api-custom-json` without a Rapier top-level `api-*` feature. The exact Redot JSON records both virtual object returns with no non-null `meta`, so gdext correctly generates optional returns.

The complete 637-file upstream payload hash was identical before and after both attempts: `7e150baf518b72e1b9d40657035be0932e6a3098d666cfedf8bfc93749907e3b`.

Release builds, entry-symbol checks, editor/runtime tests, export, and clean-install cases were not attempted because the first compile gate failed. The smallest candidate remediation is a downstream-only `redot-compat` feature that selects the already-existing optional-return implementation for 2D and 3D without enabling or forwarding an upstream Godot API feature. That patch has not been applied.
