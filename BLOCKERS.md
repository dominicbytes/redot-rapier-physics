# Blockers and gates

## Current promotion blockers

All local automated Rapier2D implementation gates pass for archive SHA-256 `af8ec56c054981c3c699f166efd91ae1685fda18a87d67762603e609d984b258`. The candidate remains unpublished until all three external promotion gates close:

1. Retained real downstream-project confirmation on Windows and Linux, or the narrowly scoped owner waiver already defined below.
2. A public run of the SHA-pinned workflow for the exact source revision, with retained evidence.
3. Explicit owner authorization for the version tag, GitHub Release/assets, and Asset Library submission.

## Resolved foundation gate: pin and adapt the porting infrastructure

- Status: PASS on 2026-08-11
- Source: `../redot-porting-infrastructure`
- Actual: the supplied template matches the Redot 26.2/API 4.5.2/single-precision identity and provides deterministic desktop CI/package/release contracts, but it is a non-Git local snapshot built around one C++/SCons/`redot-cpp` addon.
- Requirement: freeze the approved snapshot by content hash or canonical commit, adopt its language-neutral contract at the Rapier repository root, replace the compile adapter with redot-rust/Cargo, and represent two separately packageable addons under one shared upstream/toolchain lock and one lockstep `v<upstream-version>-redot.<revision>` release tag. Each tag certifies exactly one Redot engine/API identity. Publish the exact display names `Redot Rapier Physics 2D` / `Redot Rapier Physics 3D` and slugs `redot-rapier-physics-2d` / `redot-rapier-physics-3d` while preserving `addons/godot-rapier2d` and `addons/godot-rapier3d` internally.
- Evidence required: provenance inventory, contract tests, two-addon manifest/package tests that assert the exact public names/slugs, preserved paths, and dimension mapping, upstream-derived lockstep version/tag checks, single-Redot-identity validation, and workflow validation showing no `redot-cpp` dependency in the Rapier build path.
- Result: the ordered 31-file infrastructure source manifest is frozen at `ec5f2e8fe2fe65b94a17d577043aad16b70652bf23a09930e34001710b2ddf54`; `porting.json`, `redot.lock.json`, `PORT_MATRIX.md`, the Rust/Cargo adapter, external consumer path, and Windows/Linux contract are adopted; all 11 local contract tests pass; macOS is explicitly deferred; Rapier2D product metadata is enabled while release packaging remains disabled.

## Resolved implementation gate: P7-G0 incompatibility and bounded remediation

- Status: unchanged-source FAIL retained; owner-authorized bounded remediation PASS on 2026-08-11
- Target: Godot Rapier Physics `v0.35.2` / `172c66f5a88bf1164c2b8cf2d775ed889edefd75`
- Requirement: build and run unchanged crate source for 2D and 3D, debug and release, through the pinned Redot Rust compatibility layer and exact API JSON.
- Base API contract: Rapier top-level `single-dim2` or `single-dim3`, plus dependency-qualified `godot/api-custom-json`; no Rapier top-level `api-*` or `api-custom` feature. Test `register-docs`, `serde-serialize`, and solver `parallel` as explicit non-API profiles after the minimal builds.
- Evidence required: complete tracked-source hashes, resolved dependency graph, actual Cargo features/fingerprints, 2D/3D entry symbols, editor load, real collisions, backend selection, unchanged-default controls, export, and clean-install scenarios.
- Result: both minimal debug profiles resolved the pinned gdext 0.5.5 family and verified `api-custom-json`, then failed at the same `_get_space_state` return-nullability mismatch. The exact Redot JSON generates `Option<Gd<PhysicsDirectSpaceState2D/3D>>`; unchanged v0.35.2 selects `Gd<...>` when no top-level Rapier API feature is enabled. The complete 637-file source hash remained unchanged before and after both attempts.
- Evidence: `docs/gamedev/evidence/p7-g0-unchanged-v0.35.2.json` and `.md`.
- Remediation: the owner authorized an empty downstream `redot-compat` feature selecting only the existing optional-return branch for 2D and 3D, without forwarding a Godot API feature or mutating the JSON. Minimal 2D/3D debug/release builds pass. Full-feature Rapier2D editor/debug/release, Clippy, unit, feature, regression, package, export, and runtime gates pass on Windows and Linux.
- Evidence: `docs/gamedev/evidence/p7-g0-redot-compat-result.json`, the per-profile JSON reports, and the consolidated desktop-package validation report.
- Boundary: this resolves compatibility and the local automated Rapier2D product matrix. It does not authorize Rapier3D or publication.

## Resolved source selection: v0.35.2 pinned for this release line

- Status: PASS and owner-fixed on 2026-08-12
- Current result: on 2026-08-12, the official plugin releases page marks `v0.35.2` at `172c66f5a88bf1164c2b8cf2d775ed889edefd75` latest, and the official Dimforge tags page lists `v0.35.1` as the newest stable Rapier library tag. The selected committed lock matches that version and its registry checksum.
- Requirement: use exact plugin `v0.35.2` and its committed Rapier 0.35.1 lock for this release line. Do not float dependencies or reopen the candidate merely because a newer upstream appears.
- Update rule: evaluate newer stable plugin/Rapier releases in a later planned Redot cycle with a new compatibility, parity, and evidence pass.
- Post-release maintenance rule: monitor every official upstream stable plugin and Rapier crate release and begin a recorded evaluation promptly. Routine publication cycles open only with planned stable Redot releases, expected roughly quarterly; retain the current supported pin until the newer Redot-specific candidate passes the complete applicable gate matrix, and document the evaluated version, disposition, target cycle, blockers, and any temporary upstream lag.
- Support-window rule: routine maintenance applies only to the newest published Redot-specific plugin line. Older releases remain downloadable with their exact compatibility records but receive no ordinary fixes, dependency updates, or feature backports.
- Repository-intake rule: the owner reviews pull requests and issues between Redot cycles and records their disposition and target cycle when applicable. Review is best-effort and does not bypass evidence, create a response-time SLA, or force an out-of-cycle release.
- Emergency-release rule: only a confirmed security defect, data-loss defect, or release-blocking crash may open an out-of-cycle patch on the current supported line. Keep the remediation minimal, exclude features and routine dependency adoption, and run the complete applicable validation and publication matrix; the emergency label waives timing only.

## Resolved local packaging gate: staged Redot descriptors and installables

- Status: PASS locally on Windows x86-64 and Linux x86-64
- Actual: both staged `.gdextension` descriptors now declare `compatibility_minimum = "4.5"`, `reloadable = false`, and only Windows/Linux x86-64 editor/debug/release mappings. Exact display names, versions, entry symbols, and preserved paths pass the contract validator.
- Result: the deterministic 58-file package reproduces byte-for-byte, selected/default clean installs pass on both platforms, and all four official-template debug/release exports launch and pass the packaged query. Rapier3D packaging stays disabled.

## Resolved local Rapier2D gate: full applicable upstream parity

- Status: PASS; see `docs/gamedev/rapier2d-parity-ledger.md`
- Requirement: inventory every 2D capability in the pinned upstream source and verify the complete applicable surface on Redot 26.2, including PhysicsServer2D behavior, nodes/resources, shapes, bodies, areas/spaces, queries/callbacks, joints, settings/profiling, fluids/effects/particle operations, and state export/import/restore.
- Disposition rule: each parity-ledger row must be `Parity PASS`, `Not applicable` with reproducible technical evidence, or covered by an explicit owner-approved release waiver.
- Prohibited fallback: shipping a minimal/core-only package, labeling missing applicable features as previews, or silently scheduling them for later feature releases.

## Resolved local platform gate: Windows and Linux

- Status: PASS for the local candidate; public CI remains a promotion gate
- Required: Windows x86-64 and Linux x86-64 editor, template-debug, and template-release artifacts; full parity, clean install, export, runtime, package, checksum, and notice gates pass on both.
- Deferred: macOS, web, Android, iOS, other architectures, and double precision.
- Infrastructure adaptation: replace the base template's mandatory Windows/Linux/macOS matrix with an explicit Windows/Linux required set and a disabled/deferred macOS gate.

## Resolved determinism gate: identical Windows/Linux hashes

- Status: PASS; three Windows and three Linux runs match at every checkpoint and final state
- Required profile: pinned single-precision Rapier2D build with solver parallelism and Redot separate-thread execution disabled, plus frozen toolchain, dependencies, compiler settings, seed, initial state, input stream, timestep, frame count, and stable state encoding.
- Acceptance: repeated same-platform runs and the Windows/Linux comparison produce identical checkpoint and final hashes.
- Evidence: canonical inputs, environment metadata, hashes, logs, and first-divergence diagnostics are retained.
- Parallel profile: correctness, stability, repeatability, export, performance, and shutdown/restart behavior remain required, but no cross-platform byte-equality claim is made without separate proof.

## Resolved performance gate: guard against pathological or material regressions

- Status: PASS on Windows and Linux under the frozen guardrail protocol; this is not a universal performance-improvement claim
- Policy: Rapier2D is not required to match or beat Redot's default backend in every benchmark.
- Hard failures: crashes or hangs, physics correctness or stability failures, memory leaks or unbounded growth, workload failures hidden by aggregate results, and material unexplained frame-time or memory regressions beyond the frozen thresholds.
- Protocol: benchmark identical small, medium, high-body-count, and fluid workloads; capture controlled baselines first; then freeze workload definitions, environment, warm-up, sample counts, aggregation, and numerical guardrail thresholds before release-candidate comparison.
- Evidence: retain and publish raw timings and memory results, per-workload outcomes, configuration metadata, thresholds with their freeze timestamp, and explanations for accepted variance.

## Active Rapier3D product gate: add capability beyond Redot Jolt

- Status: not a Rapier2D planning or release blocker; blocks Rapier3D product implementation and publication
- Requirement: demonstrate at least one material, testable user-facing capability that the pinned Redot Jolt backend does not provide.
- Insufficient evidence: compatibility, ordinary parity, an alternate implementation, or benchmark equivalence alone.
- Rollback boundary: rollback or deterministic replay may support the case, but rollback alone fails this gate. A rollback-only result becomes a separate future standalone plugin candidate outside this repository's scope.
- Protocol: name the proposed differentiator first; freeze Jolt and Rapier configurations and a comparable scenario; demonstrate the added capability end to end; record remaining parity gaps, performance cost, and maintenance cost; obtain owner approval.
- Failure rule: if no qualifying capability exists, record a no-go and do not publish Rapier3D. Rapier2D proceeds independently.

## Resolved local release gate: dependency notices and reproducibility

- Status: PASS locally; public durable CI evidence remains a promotion blocker
- Requirement: generate an exact-feature license report, include the MPL-2.0 source-availability notice for the pinned gdext fork, pin workflow actions, use locked Cargo resolution, and retain durable evidence.
- Actual: the package adds `THIRDPARTY-REDOT.txt` and `LICENSE-MPL-2.0.txt`; the exact-feature report covers 87 packages and 57 unique license texts, and the SPDX 2.3 SBOM covers the same 87-package graph. Workflow actions are SHA-pinned and Cargo uses locked resolution.
- Additional requirement: launch and validate a release export for each addon on every claimed desktop target; the base infrastructure fixture verifies release artifact presence but only runs editor and debug-runtime smoke.
- Versioning requirement: every artifact published from a release uses the same repository version/tag in the `v<upstream-version>-redot.<revision>` scheme. The upstream component must equal the pinned Rapier source; the downstream revision increments for port-only releases and resets to `redot.1` on an upstream change. Rapier2D-only releases must contain no Rapier3D artifact; after Rapier3D becomes public, both packages are rebuilt, retested, versioned, and published together.
- Redot support requirement: every release names exactly one certified Redot engine commit/API identity. The first target is Redot 26.2/API 4.5.2. Supporting a different Redot version requires a new tag and full Windows/Linux validation; do not publish a multi-version compatibility claim from one evidence set.
- Public identity requirement: every published 2D artifact uses `Redot Rapier Physics 2D` and `redot-rapier-physics-2d`; an approved 3D artifact uses `Redot Rapier Physics 3D` and `redot-rapier-physics-3d`. Release promotion must reject mismatched names, slugs, dimensions, or internal paths, and must continue rejecting any Rapier3D artifact before approval.

## Active distribution gate: GitHub Releases and Redot Asset Library

- Status: not a planning blocker; release-blocking
- Required channels: publish every approved package through GitHub Releases and the Redot Asset Library. GitHub is the canonical release, evidence, checksum, attestation, and support record.
- Asset Library constraint: the catalog derives its download from a repository URL and full commit rather than an attached release asset. Create an immutable package-only commit in the same repository for each approved dimension and exact Redot version; never point the catalog at a moving branch.
- Payload boundary: each installable and catalog commit contains only the dimension's runtime addon plus its README and complete legal notices. Examples, parity fixtures, and test projects are separate GitHub companion assets and must not enter the catalog payload.
- Publication posture: create no public beta, preview, or RC package. Unpublished internal candidates may be tested, but the first public GitHub package must be marked non-prerelease and the Asset Library receives only the validated stable payload.
- Equality requirement: build and stage once. Compare the catalog commit's installed addon file paths and per-file SHA-256 values with the matching GitHub asset; any missing, extra, or changed installed file blocks publication. Outer archive metadata may differ and is excluded from this comparison.
- Entry rule: submit separate entries for `Redot Rapier Physics 2D` and an approved `Redot Rapier Physics 3D`. The initial release has no 3D entry. Each entry must match the lockstep package version, exact certified Redot version, license, README, internal addon path, and support links.
- Order: publish and validate GitHub first, then submit the matching commit to the Asset Library's manual review queue. A catalog rejection does not authorize changing the package payload without creating and revalidating a new downstream release.

## Active private downstream stable gate: Windows and Linux confirmation

- Status: not a planning blocker; release-blocking unless the narrowly scoped tester-availability waiver is retained
- Requirement: after all automated gates pass and before public stable publication, install the exact staged candidate in a real downstream project on Windows x86-64 and Linux x86-64. On each platform, explicitly select Rapier, exercise representative collision or query behavior, export the project, launch the exported release, and review errors and warnings.
- Evidence identity: retain the downstream project or fixture identity, candidate package SHA-256 and tag, exact Redot engine/API identity, platform, commands or actions, tester, and observed results. The confirmed package bytes must be the same bytes promoted to GitHub and mirrored to the Asset Library payload.
- Failure rule: any failed or unexplained confirmation keeps the candidate unpublished until fixed and retested.
- Waiver boundary: only lack of a suitable downstream tester or project may be waived, through explicit retained owner approval that names the missing confirmation, reason, and residual risk. This waiver cannot bypass compatibility, parity, platform, determinism, performance, packaging, legal, CI, export, runtime, or channel-equality gates.

## Partially resolved publication setup

- Status: GitHub authentication and public fork creation resolved on 2026-08-12; stable release setup remains incomplete
- Result: `https://github.com/dominicbytes/godot-rapier-physics` is a public fork of `appsinacup/godot-rapier-physics`, and source publication to `redot-26.2` is owner-authorized.
- Remaining requirement: authenticate the Redot Asset Library account and obtain explicit authorization before creating the version tag, GitHub Release/assets, or catalog submission.

## Resolved prerequisite gates

- Exact Redot API inputs are present under `plugins/api/redot-26.2/4f5b14aba-single-windows-x86_64/` with recorded hashes.
- The shared Rust/API compatibility layer is public and has successful Windows, Linux, and native macOS smoke/clean-install CI at pinned commit `18ad5c538c452b8640420366794354e3ed48f205`.
- The local Redot console executable reports `26.2.stable.official.4f5b14aba`, and both locked API artifacts passed SHA-256 validation.
