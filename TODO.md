# TODO

## Preflight

- [x] Pin the Redot 26.2 engine/API identity and hashes.
- [x] Resolve the shared Redot Rust compatibility prerequisite.
- [x] Select Rapier `v0.35.2` as the conditional source target and record the narrow `v0.8.40` 2D floor.
- [x] Refresh the preflight report, implementation plan, decisions, blockers, and source-of-truth workbook.
- [x] Confirm one repository with two independently installable addons, with Rapier2D released first.
- [x] Define `../redot-porting-infrastructure` as the required repository-level foundation and record its Rust/two-addon adaptation boundary.
- [x] Make full applicable upstream Rapier2D feature parity a first-public-release gate with no intentional feature trickle.
- [x] Limit the first public release to mandatory Windows x86-64 and Linux x86-64 packages; defer macOS and other targets.
- [x] Require exact Windows/Linux replay-hash equality for a designated single-threaded deterministic Rapier2D profile.
- [x] Use a performance guardrail instead of requiring Rapier2D to match or beat Redot's default backend in every benchmark.
- [x] Require Rapier3D to add a material, testable user-facing capability beyond Redot Jolt; compatibility, parity, or benchmark equivalence alone is insufficient.
- [x] Treat rollback/replay as supporting Rapier3D value only; if it is the sole differentiator, record a 3D no-go and keep a standalone rollback plugin outside this plan.
- [x] Preserve the upstream `addons/godot-rapier2d` and `addons/godot-rapier3d` paths while using Redot-branded public package and display identity.
- [x] Use one lockstep repository version/tag for published artifacts, without creating a Rapier3D package before the 3D gate passes.
- [x] Use upstream-derived Redot revision tags beginning with `v0.35.2-redot.1`; increment for downstream-only releases and reset to `redot.1` on an upstream change.
- [x] Certify each plugin release for one exact Redot engine/API identity, beginning with Redot 26.2/API 4.5.2; require a separately validated downstream tag for another Redot version.
- [x] Use public display names `Redot Rapier Physics 2D` and `Redot Rapier Physics 3D` with artifact slugs `redot-rapier-physics-2d` and `redot-rapier-physics-3d`, while preserving the upstream internal addon paths.
- [x] Publish approved packages through both GitHub Releases and the Redot Asset Library, with GitHub as the canonical release/evidence record and exact installed-payload equality across channels.
- [x] Verify that plugin `v0.35.2` and locked `rapier2d`/`rapier3d` `0.35.1` are the latest stable releases as of 2026-08-12.
- [x] Keep each installable lean with only the runtime addon, README, and license; publish examples, parity fixtures, and test projects as separate GitHub release assets.
- [x] Publish directly to stable after all gates pass; create no public beta/RC package and no prerelease Asset Library entry.
- [x] Require retained private downstream install, runtime, export, and exported-release confirmation for the exact candidate on both Windows and Linux before stable publication, with a narrow owner waiver only when no suitable tester or project is available.
- [x] Monitor and promptly evaluate every upstream stable plugin and Rapier crate release without promising a fixed Redot publication deadline; publish only after the complete applicable gate matrix passes.
- [x] Provide routine maintenance only for the newest published Redot-specific plugin line; retain older releases without routine backports.
- [x] Open routine plugin update cycles with planned stable Redot releases, expected roughly quarterly, and review repository pull requests and issues between cycles.
- [x] Allow narrowly scoped out-of-cycle patches on the current supported line for confirmed security, data-loss, or release-blocking crash defects while retaining the full applicable gate matrix.
- [x] Receive explicit owner approval, close the planning phase, and authorize implementation beginning with MS-022 while retaining the P7-G0 source-edit guard.

## First implementation gate

- [x] Freeze the approved porting-infrastructure snapshot by content inventory/hash or canonical commit, then adopt its language-neutral contract at the Rapier repository root.
- [x] Replace the fixture's C++/SCons/`redot-cpp` build adapter with a redot-rust/Cargo adapter and extend the contract from one addon to two separately packageable addon records under one shared lock, mapped to the preserved upstream addon paths.
- [x] Adapt and test the infrastructure platform contract so Windows and Linux are required while macOS is explicitly disabled/deferred.
- [x] Extend the release contract so every tag names exactly one Redot engine commit/API identity and rejects missing, multiple, or mismatched support identities.
- [x] Encode and test the exact display-name, artifact-slug, dimension, and preserved internal-path mapping for both addon records.
- [x] Create an external consumer harness that pins Rapier `172c66f5a88bf1164c2b8cf2d775ed889edefd75` and patches crates.io `godot` to gdext `637cef73172bba23850131acd8583b0c72ebf0c7`.
- [x] Immediately before source freeze, repeat the official stable-release checks for the plugin and both Rapier crates; if any newer stable exists, refresh the lock and compatibility plan before continuing.
- [ ] Define the auditable maintenance record created for each newly discovered stable plugin or Rapier crate release, including evaluated identities, current pin, compatibility/parity impact, disposition, blockers, and evidence links.
- [ ] Define the repository issue/pull-request triage record, including disposition, target Redot cycle when accepted or deferred, evidence requirements, and links, without promising a response-time SLA.
- [ ] Encode the current supported-line marker in release notes, documentation, and support records; label older exact-Redot releases as available but not routinely maintained.
- [x] Hash the complete tracked v0.35.2 payload before and after the probe; do not reuse the narrow v0.8.40 hash list.
- [x] Retain the unchanged-source debug failure for both dimensions, obtain owner approval for the bounded `redot-compat` selector, and pass minimal 2D/3D debug and release builds without a top-level API feature.
- [x] Capture the complete unchanged source boundary, downstream Cargo lock, resolved gdext identity, actual feature profiles, and expected dimension-specific entry-symbol contract.
- [x] Pass full-feature Rapier2D debug/release builds, Clippy, exact Redot editor import, focused runtime selection/query smoke, and the upstream 39-scene regression suite on Windows x86-64.
- [x] Run the pinned Linux x86-64 job locally and retain its full-feature build, import, focused smoke, regression, and binary-hash evidence. A public workflow run remains a promotion gate.
- [x] Verify unchanged-default/switch-back controls, export, exported-release launch, and clean install for Rapier2D on both required platforms; retain 3D as compatibility-only.
- [x] If the gate fails, isolate the smallest incompatibility before proposing any source patch; the first mismatch is the 2D/3D `_get_space_state` return-nullability branch, and the failed-build evidence is retained without a patch.

## Port milestones after the gate

- [x] Stage Redot-compatible 2D packaging and prove registration, selection, switch-back, and standard-physics controls.
- [x] Build a stable-ID parity ledger from the pinned upstream 2D public surface and regression fixtures.
- [x] Prove every applicable upstream 2D capability, including fluids/effects/particle operations, serialization/restore, nodes/resources, physics-server behavior, queries, joints, settings, determinism, stacking, and no-ghost behavior.
- [x] Block release on every missing or untested applicable parity row unless the owner explicitly approves a documented waiver; the local candidate requires no feature waiver.
- [x] Pass the complete parity, clean-install, export, runtime, and packaging matrix on both Windows x86-64 and Linux x86-64.
- [x] Freeze the deterministic-profile manifest and canonical replay inputs, including stable sorted state encoding and checkpoint schedule.
- [x] Prove identical same-platform and Windows/Linux deterministic-profile hashes; retain first-divergence diagnostics.
- [x] Test the parallel profile independently for correctness, stability, repeatability, performance, export, and race-sensitive shutdown without overclaiming cross-platform hash equality.
- [x] Capture controlled Redot-default and Rapier2D baselines, then freeze workload definitions and numerical guardrail thresholds before release-candidate comparison.
- [x] Block release on crashes or hangs, physics correctness or stability failures, leaks or unbounded memory growth, and material unexplained frame-time or memory regressions; retain raw comparison results.
- [ ] Freeze a proposed Rapier3D differentiator and a Jolt/Rapier comparison scenario, then prove a material added capability beyond any rollback-only benefit or record an explicit no-go before product implementation.
- [x] Run cross-platform determinism and performance protocols on supported desktop targets.
- [x] Complete exact-feature license/MPL notices, reproducible release builds, and clean-install packages. Public CI/publication evidence remains open.
- [x] Validate that every candidate artifact carries the same version/tag identity and that Rapier3D is omitted before approval.
- [x] Validate that archives, manifests, documentation, checksums, and support records use the approved public name and slug for Rapier2D.
- [x] Validate the tag parser and release metadata so the upstream component matches the pinned source and the Redot revision advances monotonically.
- [x] Validate that manifests, checksums, attestations, and both platform packages resolve to the one certified Redot/API identity for the tag.
- [ ] Generate one lean staged installable payload per approved dimension, publish its GitHub asset, and create a same-repository package-only Asset Library commit whose installed-file path/SHA-256 manifest matches exactly.
- [ ] Publish dimension-specific examples, parity fixtures, and test projects as separate GitHub companion assets tied to the same tag and Redot identity; exclude them from installables and catalog commits.
- [ ] Validate one Asset Library entry per approved dimension and exact Redot version; omit the Rapier3D entry until its product gate passes.
- [ ] Validate that release automation marks the first public GitHub release as non-prerelease, publishes no beta/RC assets, and exposes no catalog commit before stable promotion.
- [ ] Collect and retain real downstream clean-install, backend-selection, representative runtime, export, exported-release launch, and error/warning-review evidence for the exact candidate package on Windows x86-64 and Linux x86-64.
- [ ] If a suitable downstream tester or project is unavailable on either required platform, retain an explicit owner waiver naming the missing confirmation, reason, and residual risk; do not use it to bypass any automated release gate.
- [x] Add and pass release-export runtime launches for Rapier2D; repeat the same gate for Rapier3D only if its product gate is approved.

## Publication

- [ ] Run the SHA-pinned workflow publicly for the exact candidate revision and retain its evidence.
- [x] Obtain explicit owner authorization to create the public fork and commit/push the Redot source branch.
- [ ] Obtain explicit owner authorization before creating the version tag, GitHub Release/assets, or Asset Library submission.
- [x] Authenticate the downstream GitHub account and create the public `dominicbytes/godot-rapier-physics` fork.
- [ ] Authenticate the Redot Asset Library account and submit the validated Rapier2D catalog entry only after the canonical stable GitHub release is published.
