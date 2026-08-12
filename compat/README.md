# Redot compatibility probe

This directory contains downstream-only Redot inputs. The clean upstream checkout remains separate so the original P7-G0 result and source boundary can be reproduced.

The allowed Cargo feature routes are:

- Rapier2D shipping profile: top-level `single-dim2`, `redot-compat`, `serde-serialize`, `parallel`, and `register-docs`, plus dependency feature `godot/api-custom-json`.
- Rapier3D compatibility probe: top-level `single-dim3` and `redot-compat`, plus dependency feature `godot/api-custom-json`.

`redot-compat` selects only the existing nullable `_get_space_state` implementation and does not forward a feature to `godot`. Do not enable Rapier's top-level `api-4-5`, `api-custom`, or any other `api-*` feature. The exact Redot JSON supplied through `GDRUST_GODOT_API_JSON` drives all generated signatures.

Use `scripts/redot_porting.py` to validate the shared contract, hash the complete tracked source payload, and prepare an external consumer copy. Cargo may generate a consumer lock in that copy; the pinned source checkout must remain clean and byte-identical before and after the probe.
