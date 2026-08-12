# Rapier2D parity ledger

Status: **PASS for the local `0.35.2-redot.1` candidate** on Redot 26.2, Windows x86-64, and Linux x86-64.

This ledger answers the first-release requirement that Rapier2D retain every applicable product capability of upstream Godot Rapier Physics `v0.35.2`. It does not claim that inherited upstream defects are fixed. The byte-level parity gate compared 96 runtime source files and 50 addon files against upstream commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75`; the only runtime differences are the two authorized `redot-compat` cfg selectors, with no deleted or deferred 2D implementation.

| ID | Upstream 2D capability | Candidate status | Acceptance evidence |
| --- | --- | --- | --- |
| RP2D-001 | `PhysicsServer2D` backend registration and explicit `Rapier2D` selection | PASS | Windows/Linux clean-install selected-backend results and feature-parity scenes |
| RP2D-002 | Additive install; unchanged projects keep the default backend | PASS | Windows/Linux default-control clean-install results |
| RP2D-003 | Static, rigid, animatable, and character bodies | PASS | Upstream 39-scene regression, Redot unit scenes, and unchanged runtime-source comparison |
| RP2D-004 | Areas, gravity/damping overrides, monitoring, and collision layers/masks | PASS | Upstream regression plus feature-parity class/method surface checks |
| RP2D-005 | Circle, rectangle, capsule, segment, separation-ray, convex, concave, and world-boundary shapes | PASS | Upstream regression and byte-identical upstream shape implementation |
| RP2D-006 | Contacts, body/area callbacks, collision exceptions, one-way collision, and motion tests | PASS | Upstream regression and exact Redot API-driven method signatures |
| RP2D-007 | Point, ray, shape, and motion/direct-space queries | PASS | Feature smoke, clean-install point query, and upstream regression |
| RP2D-008 | Pin, damped-spring, groove, fixed, and rope joints | PASS | Redot joint unit scenes, upstream regression, and unchanged joint implementation |
| RP2D-009 | Continuous collision detection and separation-ray behavior | PASS (upstream-equivalent) | Regression classification retains two declared upstream moving-body CCD expectations; downstream adds no failure |
| RP2D-010 | Custom 2D nodes, resources, icons, and editor registration | PASS | All 14 extension classes and 14 addon scripts load on Windows/Linux; addon files match upstream |
| RP2D-011 | Rapier project settings and solver controls | PASS | Feature smoke validates 23 settings; editor profile includes documentation registration |
| RP2D-012 | Fluid worlds, fluid particles, boundaries, interactions, and effects | PASS | Feature smoke exercises fluids/effects/particles; 2048-particle guardrail workload passes both platforms |
| RP2D-013 | State cache, export/import, serialization, and restore | PASS | Feature smoke exercises JSON, Base64, and Bincode state paths; Rust unit suite passes 76/76 |
| RP2D-014 | Deterministic replay profile | PASS | Three Windows and three Linux 300-frame runs match exactly: replay SHA-256 `9f1b106595ac6361a7676f6f488e9929e953430c5ac8eccce499ba722eb67928` |
| RP2D-015 | Parallel solver build/profile | PASS | `parallel` is present in editor/debug/release candidate profiles; correctness/regression and performance gates pass on both platforms. Cross-platform hash equality is intentionally claimed only for the single-threaded profile. |
| RP2D-016 | Stacking, sleeping/waking, forces, impulses, velocities, and material response | PASS | Upstream regression, Redot unit scenes, and unchanged runtime-source comparison |
| RP2D-017 | No-ghost/removal lifecycle and representative regression behavior | PASS | Both platform regressions complete 208/210 declared monitors, two expected failures, and six improvements without unexplained errors |
| RP2D-018 | Editor, template-debug, and template-release native profiles | PASS | Six distinct native artifacts load from the deterministic package; all four exported products run successfully |
| RP2D-019 | Windows x86-64 and Linux x86-64 package/install/export operation | PASS | Exact archive clean-installs with selected and default backends on both platforms; debug/release exports and runtime launches pass |
| RP2D-020 | Upstream runtime and addon payload parity | PASS | `rapier2d-upstream-parity.json`: 96 runtime files, 50 addon files, two authorized cfg deltas, zero unexpected deltas |
| RP2D-021 | Distribution notices and exact-feature dependency record | PASS | 87-package exact-feature license report, SPDX 2.3 SBOM, MIT/MPL notices, and source-availability record included |
| RP2D-022 | Upstream `profiling` feature | N/A | Development instrumentation is not enabled in upstream release profiles and is not a user-facing 2D product capability. It remains available for developer builds rather than becoming a deferred release feature. |

## Evidence set

- `docs/gamedev/evidence/rapier2d-upstream-parity.json`
- `docs/gamedev/evidence/rapier2d-final-windows-feature-parity.log`
- `docs/gamedev/evidence/rapier2d-final-linux-feature-parity.log`
- `docs/gamedev/evidence/rapier2d-final-win-regression.log`
- `docs/gamedev/evidence/rapier2d-final-linux-regression.log`
- `docs/gamedev/evidence/rapier2d-determinism-cross-platform.json`
- `docs/gamedev/evidence/rapier2d-performance-guardrail-windows.json`
- `docs/gamedev/evidence/rapier2d-performance-guardrail-linux.json`
- `docs/gamedev/evidence/rapier2d-desktop-package-validation.json`

## Deferred variants, not missing 2D parity

macOS, web, mobile, other CPU architectures, and double precision are outside the first-release platform/variant contract. Rapier3D is a separate installable and remains unpublished unless it demonstrates material user-facing value beyond Redot Jolt. Neither category is a missing Rapier2D feature.
