# Preflight report: Godot Rapier Physics for Redot

## Outcome

| Field | Result |
|---|---|
| Research date | 2026-08-10 |
| Program priority | 7 |
| Planning disposition | **CLOSED / OWNER APPROVED on 2026-08-11** |
| Implementation disposition | **Local Rapier2D `0.35.2-redot.1` implementation and automated Windows/Linux matrix complete** |
| Release disposition | **NO TAG OR RELEASE; blocked on downstream confirmation/waiver, public CI, and explicit stable-release authorization** |
| Conditional source target | Godot Rapier Physics `v0.35.2`, commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75`, tree `40db8bc1e0c0b04391c8458c518e6889713b851d` |
| Shared compatibility input | `dominicbytes/redot-rust` commit `18ad5c538c452b8640420366794354e3ed48f205` |
| Target API | Redot 26.2 stable, compatible Godot API 4.5.2, single precision |
| Legacy research checkout | `ebda960c920f73cf34823a2f4efe5a7a585a627e` (v0.35.1 era; source left unchanged) |
| Implementation branch | Public fork `dominicbytes/godot-rapier-physics`, branch `redot-26.2`, based on exact upstream `v0.35.2` |

The old Priority 6 planning blocker is resolved: the public [redot-rust repository](https://github.com/dominicbytes/redot-rust) pins the engine/API/gdext contract, and [CI run 31424543055](https://github.com/dominicbytes/redot-rust/actions/runs/31424543055) passed its Windows, Linux, and native macOS smoke and clean-install jobs. That evidence proves the shared Rust compatibility layer, not Rapier.

Godot Rapier Physics [v0.35.2](https://github.com/appsinacup/godot-rapier-physics/releases/tag/v0.35.2) is the selected baseline because it removes an unavailable gdext call from the local v0.35.1-era source, its committed lock resolves the Godot Rust family to 0.5.5, and its [upstream CI run](https://github.com/appsinacup/godot-rapier-physics/actions/runs/31365583361) is green. Unchanged source failed at one isolated Redot nullability boundary. After retaining that evidence, the owner authorized a three-file production delta: an empty `redot-compat` selector and one cfg selection in each existing 2D/3D nullable `_get_space_state` branch. Minimal compatibility builds pass, and the complete local Rapier2D Windows/Linux build, test, package, export, determinism, performance, and legal matrix now passes; release promotion remains gated.

No candidate plugin code was built or executed during the research-only preflight itself. The implementation results below were added after planning closed.

### 2026-08-12 implementation and freshness addendum

The official Godot Rapier Physics [releases page](https://github.com/appsinacup/godot-rapier-physics/releases) marks plugin `v0.35.2` at `172c66f5a88bf1164c2b8cf2d775ed889edefd75` latest. The official [Dimforge Rapier tags](https://github.com/dimforge/rapier/tags) list `v0.35.1` as the newest stable library tag. The selected plugin's committed lock matches `rapier2d`/`rapier3d` 0.35.1 and their registry checksums. The owner subsequently fixed `v0.35.2` as this release line's input; later upstream versions are handled in a future update rather than reopening this candidate.

The deterministic 58-file candidate archive is `redot-rapier-physics-2d-0.35.2-redot.1.zip`, SHA-256 `af8ec56c054981c3c699f166efd91ae1685fda18a87d67762603e609d984b258`. It reproduces byte-for-byte, includes all six Windows/Linux editor/debug/release libraries and complete legal notices, clean-installs with both selected and default backend controls, and exports/runs debug and release products on both required platforms. Full upstream 2D parity, six-run cross-platform deterministic replay, performance guardrails, 76 Rust unit tests, Redot unit/feature scenes, the 39-scene regression suite, the 87-package exact-feature license report, and the SPDX 2.3 SBOM all pass. See `rapier2d-parity-ledger.md` and `evidence/rapier2d-desktop-package-validation.json`.

The release plan now uses both GitHub Releases and the [Redot Asset Library](https://docs.redotengine.org/community/asset_library/submitting_to_assetlib). Redot's catalog computes its download from a repository URL and full commit and accepts one engine version per entry; it does not consume an attached GitHub release asset. GitHub remains the canonical release/evidence record, while each catalog entry uses a package-only immutable commit from the same repository. The installed addon path/SHA-256 manifest must match the corresponding GitHub asset exactly, and Rapier3D receives no entry before its product gate passes. Each installable remains lean—runtime addon plus README and complete legal notices—while examples, parity fixtures, and test projects are separate GitHub companion assets and never enter the catalog payload. Publication goes directly to stable after all gates: internal candidate artifacts may be tested privately, but no public beta/RC release or prerelease catalog entry is permitted. Before that stable publication, the exact candidate package must also receive retained real downstream install, selection, representative runtime, export, and exported-release confirmation on both Windows and Linux; only lack of a suitable tester or project permits an explicit owner waiver, and that waiver does not bypass automated gates.

The maintenance policy continues that freshness requirement after launch: every official upstream stable plugin or Rapier crate release receives a prompt recorded evaluation, but no fixed Redot publication deadline. The current pin remains authoritative until a newer candidate passes the complete applicable gates, and project records must disclose the newest evaluated versions, current pin, disposition, blockers, and any temporary lag.

Routine maintenance is limited to the newest published Redot-specific plugin line. Planned stable Redot releases, expected roughly quarterly, open routine update cycles; upstream stable changes and accepted repository work are queued for those cycles, while full gates still determine publication. The owner reviews repository pull requests and issues between cycles and records their disposition without promising an immediate release or response-time SLA. Older exact-Redot releases remain available and documented but do not receive ordinary backports.

A narrow emergency exception permits an out-of-cycle patch on the current supported line for a confirmed security defect, data-loss defect, or release-blocking crash. It waives only the quarterly timing rule: the patch remains minimal, excludes features and routine dependency upgrades, and must pass the complete applicable release matrix.

## Research brief

The preflight answered six planning questions:

1. Which exact upstream, Redot, Rust, gdext, and API identities are defensible?
2. Which Cargo feature route matches the exact Redot JSON rather than an approximate Godot version label?
3. Which Rapier capabilities justify an additive backend, and which claims remain hypotheses?
4. What evidence must the first implementation gate capture, including failure and fallback rules?
5. What license, supply-chain, packaging, and platform obligations block release?
6. Which apparent alternatives should be rejected before they enter the implementation plan?

Success for preflight means the inputs are pinned, the evidence boundary is explicit, the first gate is reproducible, and no implementation claim is inferred from adjacent evidence.

## Source and dependency decision

### Selected conditional candidate

- Godot Rapier Physics plugin version: `v0.35.2`
- Tag commit: `172c66f5a88bf1164c2b8cf2d775ed889edefd75`
- Tree: `40db8bc1e0c0b04391c8458c518e6889713b851d`
- Rust: 1.94.0
- Manifest Godot dependency: `0.5.4` as a compatible semver floor
- Committed lock selection: Godot Rust family 0.5.5
- Physics/fluid crates: Rapier 0.35.1 and Salva 0.10.0 from crates.io with checksums
- Git sources in the v0.35.2 lock: none

The plugin release number and the Dimforge Rapier crate number are different: plugin `v0.35.2` still uses Rapier crates `0.35.1`.

The 2026-08-11 freshness audit confirms that those distinct numbers are both current stable identities: plugin `v0.35.2` is the latest stable plugin release, while `0.35.1` is the latest stable release of both underlying Rapier crates. The implementation gate must repeat this audit rather than treating today's result as permanent.

The release tag is lightweight, the target commit is unsigned, and GitHub reports the release as mutable. The plan therefore pins commit and tree, builds downstream from source, preserves the lock, and does not adopt upstream binaries as the Redot baseline.

### Why the local v0.35.1-era checkout is not the target

The local source calls `godot::sys::is_initialized()`, which is absent from the pinned gdext 0.5.5 source. v0.35.2 removes that use and aligns its locked Godot Rust dependency with the shared compatibility input. The local checkout remains useful for research, but it is superseded as the port candidate.

### Known compatibility floor

The checked-in redot-rust consumer report proves unchanged Godot Rapier Physics `v0.8.40` for Windows, 2D single precision, debug and release, with 9/9 runtime assertions and the `rapier_2d_init` entry point. It proves that the custom-JSON Redot Rust path can host one unchanged Rapier consumer. It does not prove 3D, fluids, serialization, determinism, current Rapier, or a desktop matrix.

`v0.8.40` also depended on a moving Salva branch at manifest level. It is retained only as a narrow 2D bisect floor, not as a release fallback.

## Exact Redot and Rust/API contract

### Pinned inputs

| Input | Identity |
|---|---|
| Redot engine | `4f5b14abade2239104847d03d8f9056e4467cfcd` |
| Redot release/API | 26.2 stable / compatible Godot API 4.5.2 / single precision |
| API JSON SHA-256 | `177E7796166929B2193C9CCE2FD32F59601A0147D0D1E7FE904B94E8F69F6577` |
| Interface header SHA-256 | `4CD695E86B92E2BF4E60BBE19CE137FAF41205DA1CF94F29E069AFEC0F7BF320` |
| gdext | `637cef73172bba23850131acd8583b0c72ebf0c7` on the 0.5.5 line |
| redot-rust | `18ad5c538c452b8640420366794354e3ed48f205` |
| Rust | 1.94.0 |

The exact API artifacts are stored under `plugins/api/redot-26.2/4f5b14aba-single-windows-x86_64/`. The installed Redot console reports `26.2.stable.official.4f5b14aba`; its generated API and interface hashes match the lock. The final rebuilt Windows Rapier2D DLL imports, reports `Rapier2D v0.35.2-redot.1`, passes the focused query smoke without warnings, and completes the 39-scene regression suite with `STATUS: SUCCESS`.

### Feature contract and the custom-JSON trap

The exact Redot JSON has method signatures that do not match the branches selected by Rapier's top-level API labels. In particular, `_get_space_state` is non-null in the target JSON, and the 2D one-way-collision virtual has the four-argument signature. Therefore:

- Use Rapier top-level `single-dim2` or `single-dim3` as the dimension/precision base.
- Enable [`godot/api-custom-json`](https://godot-rust.github.io/docs/gdext/master/godot/) on the Godot dependency and supply the exact JSON through `GDRUST_GODOT_API_JSON`.
- Do not enable Rapier's top-level `api-4-5`, `api-custom`, or any other top-level `api-*` feature.
- Exercise `register-docs`, `serde-serialize`, and solver `parallel` as explicit non-API feature profiles after the minimal custom-JSON builds pass.
- Test solver `parallel` on/off separately from Redot's `run_on_separate_thread` on/off. The removed `experimental-threads` release path is not a substitute for either test.

Rapier's top-level `api-4-5` selects an optional-return branch that differs from the exact target JSON. Its top-level `api-custom` selects newer virtual signatures and direct version parsing rejects Redot product major 26. The dependency-qualified custom-JSON feature lets the validated JSON drive generated signatures.

The old v0.8.40 consumer report's `final_crate_cfg = feature="api-4-5"` field is not observed evidence: the probe copies that label from its input record. Retained Cargo fingerprints show no such Rapier top-level feature. P7-G0 must inspect `cargo metadata` and compiled fingerprints directly.

## Feature scope and acceptance signals

Rapier remains additive. Untouched projects must retain their current Redot backend; explicit selection activates `Rapier2D` or an approved `Rapier3D` scope.

| Area | Planning disposition | Required evidence before a claim |
|---|---|---|
| 2D registration and standard physics | Required first slice | Clean install, explicit selection, switch-back, missing-backend handling, representative collision/query, unchanged-default control |
| Fluids | Candidate differentiator | Redot fixture with stable effect assertions; reproduce or close upstream 2D fluid concern |
| Serialization/restore | Candidate differentiator | Exact physics-server state restore plus separately documented SceneTree/node-cache synchronization behavior |
| Determinism | Required protocol, bounded claim | Fixed engine/build/features/precision/architecture/seed/timestep; repeated hashes; physics-server claim separated from whole SceneTree |
| Stacking and no-ghost behavior | Required value fixtures | Identical comparative scenes against Redot defaults, written tolerances, CCD/tunneling regressions |
| Solver parallelism | Optional desktop profile | Parallel on/off and Redot separate-thread on/off tested independently |
| 3D | Compatibility probe required; product scope optional | Explicit value/parity decision against Redot Jolt; SoftBody and joint/collision gaps documented |
| Web/mobile/double precision | Deferred variants | Separate compatibility, packaging, performance, and support decisions |

Upstream documentation is useful for hypotheses, not acceptance. The [progress page](https://godot.rapier.rs/docs/progress/) documents unsupported 3D SoftBody and asymmetric collision limits, and current issues overlap the requested value set: [dynamic CCD tunneling #610](https://github.com/appsinacup/godot-rapier-physics/issues/610), [2D fluid behavior #551](https://github.com/appsinacup/godot-rapier-physics/issues/551), [rollback desync #534](https://github.com/appsinacup/godot-rapier-physics/issues/534), [ShapeCast2D inconsistency #532](https://github.com/appsinacup/godot-rapier-physics/issues/532), and [3D CCD stutter #503](https://github.com/appsinacup/godot-rapier-physics/issues/503). These become fixture candidates, not inherited defects or assumed fixes.

Rapier's `enhanced-determinism` is enabled unconditionally on the selected physics dependencies; there is no separate downstream “deterministic build mode” to promise. Upstream cross-platform determinism evidence is encouraging, but its 3D comparison is allowed to continue on error and it does not establish a whole-game determinism guarantee.

## P7-G0: compatibility probe, not port proof

P7-G0 must run before any source or packaging adaptation. Its result label is `COMPATIBILITY_PROBE_PASS`, not `PORT_PASS`.

1. Acquire v0.35.2 separately at the pinned commit and establish safe downstream/upstream remotes. Do not repurpose the dirty v0.35.1 research checkout.
2. Hash the complete tracked source payload before and after the probe, including Cargo.lock, addon descriptors, GDScript, scenes, tests, notices, and workflows. The existing v0.8.40 probe hashes too narrow a subset and hard-codes 2D Windows tooling.
3. Externally patch crates.io `godot` to gdext `637cef73172bba23850131acd8583b0c72ebf0c7`; do not modify Rapier source for the probe.
4. Run minimal 2D and 3D custom-JSON builds in debug and release using the exact API JSON and the feature contract above.
5. Run intended desktop profiles for `register-docs`, `serde-serialize`, and solver `parallel` on/off. Record the complete actual feature graph and one gdext source.
6. Use Godot 4.5.2 as the upstream behavioral oracle where feasible, then run the same bounded fixtures on Redot 26.2. Upstream API-4.5 `cargo check` is insufficient.
7. Verify `rapier_2d_init` and `rapier_3d_init`, editor load, one real collision per dimension, explicit selection, unchanged-default controls, export, and clean install.
8. Exercise 2D-only, 3D-only, both standalone addons, switch-back, missing-backend handling, and the embedded single-main-`ExtensionLibrary` registration case.
9. Stage descriptors for the probe without accepting the upstream API-4.7 packages. Upstream 2D/3D descriptors declare `compatibility_minimum = "4.7"`; downstream packaging must prove the Redot-compatible minimum and `reloadable = false`.
10. Retain source hashes, lockfile, `cargo metadata`, fingerprints, commands, entry-symbol inspection, editor/runtime/export logs, clean-install reports, and artifact hashes.

A failure stops source work and produces a minimal incompatibility report. The v0.35.2 unchanged-source failure did so; ADR-0277 records the subsequent owner authorization for the isolated downstream selector. The remediated compatibility pass authorizes the smallest packaging adaptation, but does not prove fluids, serialization, determinism, performance, Linux, exports, or full 3D product value.

## Milestone and fallback consequences

- If v0.35.2 2D passes and 3D fails, retain v0.35.2 for 2D and defer optional 3D. Do not downgrade a working required 2D path solely because optional 3D fails.
- If the minimal custom-JSON profile passes but an intended non-API feature fails, scope that feature explicitly rather than silently changing the API route.
- If v0.35.2 fails at the API boundary, use the v0.8.40 2D proof to bisect the first incompatible revision before proposing a source patch.
- Do not mix plugin versions across dimensions without a separate complexity, maintenance, and packaging decision.
- Full Rapier3D work starts only after a measurable value/parity decision against Redot Jolt.
- Initial product claims require Windows x86-64 and Linux x86-64 only. The shared redot-rust prerequisite has broader smoke evidence, but macOS, web, mobile, double precision, and other architectures remain separate candidates for this plugin.

The detailed staged sequence and verification checks are in `implementation-plan.md`.

## License, assets, and supply chain

Planning may proceed, but release designation requires all of the following:

- Retain the Godot Rapier MIT license and notices.
- Include applicable Apache-2.0 terms/notices for Rapier and Salva, and mark modifications to Apache-covered files if any.
- Include MPL-2.0, identify gdext commit `637cef73172bba23850131acd8583b0c72ebf0c7`, and provide recipients the corresponding MPL-covered source. Invoking redot-rust tooling from a pinned checkout does not relicense unrelated port files; copied or modified MPL files remain MPL-covered.
- Generate exact-feature, per-target SBOM, license, and advisory reports for the complete locked transitive closure. Upstream `THIRDPARTY.txt` does not mention godot-rust/gdext or MPL-2.0 and is not sufficient alone.
- Treat software licenses separately from trademark or logo permission. Omit or replace branded assets unless their reuse is cleared.
- Build from the pinned source rather than mutable release artifacts; use locked dependency resolution, pin CI action SHAs, retain durable evidence, and publish checksums/attestations.

The public redot-rust workflow is sufficient prerequisite evidence for planning, but it is not yet release-grade: it uses mutable action tags, Cargo invocations omit `--locked`, evidence artifacts retain seven days, and the repository has no tag or release.

## Rejected and deferred candidates

| Candidate | Disposition | Reason |
|---|---|---|
| Local v0.35.1-era source as baseline | Reject | Stale and contains an unavailable gdext call fixed by v0.35.2 |
| Upstream v0.35.2 binaries/descriptors | Reject for Redot | Built for upstream Godot; descriptors require 4.7; provenance is not sufficient for a downstream Redot release |
| Rapier top-level `api-4-5` | Reject | Selects signatures that differ from the exact Redot JSON |
| Rapier top-level `api-custom` | Reject | Selects newer branches and rejects Redot product major 26 in direct mode |
| v0.8.40 as release baseline | Reject | Only a narrow Windows 2D compatibility floor; older moving-branch dependency history |
| Native 2D/3D engine modules | Reject for this plan | Require engine-module integration and SCons rebuild; conflict with the additive Rust plugin prerequisite |
| Replace Redot defaults | Reject | Product scope requires selectable alternatives and unchanged-default controls |
| Immediate full Rapier3D | Defer | 3D is optional and needs an approved value/parity case against Jolt |
| Initial web/mobile/double support | Defer | Requires separate bindings, packaging, performance, and support evidence |

## Query and source ledger

| Route | Result and use |
|---|---|
| Local repository inventory (`rg`, manifests, workflows, descriptors, fixtures, git identity) | Established v0.35.1-era checkout, current feature surface, separate 2D/3D entry points, API-4.7 descriptors, and existing test assets. Read-only. |
| Rapier GitHub release/API/raw files and exact-tag CI | Established v0.35.2 commit/tree, manifest/lock distinction, dependency sources, source delta, current CI, and release provenance. |
| Exact web search for `redot-rust` | Search index returned no usable result and the direct web cache missed. GitHub API/raw endpoints and the public repository/Actions pages succeeded and became the primary evidence. |
| Public redot-rust repository, raw files, and Actions run | Established commit pin, engine/API/gdext/Rust identities, workflow scope, and three-platform smoke evidence. |
| Local/public v0.8.40 consumer report and retained fingerprints | Established the narrow unchanged-source 2D floor and exposed the unverified copied `final_crate_cfg` field. |
| Pinned local Redot API JSON/interface header and installed Redot 26.2 console | Established exact hashes and target signatures; local engine identity, import, focused Rapier2D smoke, and full upstream 2D regression execution now pass on Windows. |
| Godot Rapier progress/docs/issues and Priority 7 local specification | Defined hypothesis-level features, omissions, issue-driven fixtures, additive behavior, and optional 3D scope. |
| Redot Jolt and standard backends | Established the comparison baseline for 3D value/parity and unchanged-default controls. |
| Native module repositories | Evaluated and rejected because they require rebuilding the engine rather than an additive GDExtension plugin. |
| crates.io metadata API during license audit and 2026-08-11 refresh | The earlier anonymous request was rejected under the data-access policy. A compliant identified request succeeded on 2026-08-11 and confirmed maximum-stable `rapier2d`/`rapier3d` `0.35.1`, publication metadata, and checksums. A downstream SBOM/license tool run remains a release gate. |
| Redot Asset Library submission documentation | Established that catalog downloads are computed from a repository plus full commit, one engine version is represented per entry, plugin folders should include their README/license, and submissions receive manual review. |

## Adversarial evidence audit

Three independent read-only critics challenged compatibility, evidence integrity, scope, provenance, and legal assumptions. They did not edit files, install dependencies, or execute candidate code.

### Compatibility critic

| Finding | Verdict | Resolution |
|---|---|---|
| RAP-COMP-01: v0.35.2 is the right first source candidate | PASS | Selected conditionally and pinned by tag plus commit. |
| RAP-COMP-02: “v0.35.2 uses godot 0.5.4” as an exact identity | FAIL | Records distinguish manifest floor 0.5.4 from locked 0.5.5. |
| RAP-COMP-03: the shared Rust/API prerequisite passes | PASS | Planning blocker closed; Rapier proof remains separate. |
| RAP-COMP-04: top-level `api-4-5` or `api-custom` targets Redot | FAIL | Both rejected; dependency `godot/api-custom-json` is required. |
| RAP-COMP-05: upstream package can run on Redot as shipped | BLOCKED | Reject upstream packages; prove staged Redot descriptors after P7-G0. |
| RAP-COMP-06: v0.8.40 is a known-good fallback | PASS with scope limit | Recorded only as a Windows 2D compatibility floor. |
| RAP-COMP-07: recorded `final_crate_cfg` is observed evidence | FAIL | Gate captures actual metadata/fingerprints; copied label is not cited as proof. |
| RAP-COMP-08: Rapier can remain additive | PASS | Default-backend and explicit-selection controls are mandatory. |

### Provenance and license critic

| Finding | Verdict | Resolution |
|---|---|---|
| AUD-RP-PROV-01: v0.35.2 is traceable | PASS | Commit and tree recorded. |
| AUD-RP-PROV-02: upstream release is authenticated/immutable | FAIL | Build downstream from pinned source; require attestations for release. |
| AUD-RP-DEP-03: godot 0.5.4 is exact | FAIL | Manifest floor/lock distinction corrected. |
| AUD-RP-SC-04: latest still uses moving Salva Git | PASS (claim disproved) | v0.35.2 crates.io/checksum lock recorded as an advantage. |
| AUD-RP-FLOOR-05: v0.8.40 is the preferred release baseline | FAIL | Rejected as release baseline. |
| AUD-RP-FLOOR-06: v0.8.40 is a legitimate limited floor | PASS | Narrow evidence retained with exact scope. |
| AUD-RR-PROV-07: public redot-rust has usable provenance | PASS | Full commit pin required; no mutable main. |
| AUD-RR-SCOPE-08: redot-rust is a runtime crate/current Rapier proof | FAIL | Treated only as the build/validation contract. |
| AUD-RR-SC-09: redot-rust CI is release-grade | BLOCKED | CI hardening and durable evidence added to release gate. |
| AUD-RP-LIC-10: upstream notices suffice | FAIL | Exact-feature notices and MPL source availability required. |
| AUD-RP-SEC-11: advisory/license clearance is complete | BLOCKED | SBOM, advisory, and license scans required before release. |
| AUD-RP-ASSET-12: code license clears brand assets | BLOCKED | Asset/trademark clearance or rebranding required. |

### Scope and skepticism critic

| Finding | Verdict | Resolution |
|---|---|---|
| AUD-RAPIER-SK-01: Priority 6 satisfies Priority 7 planning prerequisite | PASS | Old planning blocker closed. |
| AUD-RAPIER-SK-02: Priority 6 proves the full port | FAIL | Cross-platform smoke and narrow Rapier evidence remain separate. |
| AUD-RAPIER-SK-03: v0.35.2 is the right first candidate | PASS | Selected only for P7-G0. |
| AUD-RAPIER-SK-04: v0.35.2 works unchanged on Redot | BLOCKED | P7-G0 is the first implementation action. |
| AUD-RAPIER-SK-05: v0.8.40 is feature-complete fallback | FAIL | Retained only as a 2D bisect floor. |
| AUD-RAPIER-SK-06: current consumer probe is sufficient | FAIL | Full payload hashing, 3D symbols, portable tooling, and package evidence required. |
| AUD-RAPIER-SK-07: upstream docs prove feature fit | FAIL | Each claim receives a Redot fixture; open issues seed regressions. |
| AUD-RAPIER-SK-08: full Rapier3D is approved | BLOCKED | 2D first; explicit Jolt value/parity gate. |
| AUD-RAPIER-SK-09: a separate deterministic build mode exists | FAIL | Record unconditional enhanced-determinism and test bounded claim levels. |
| AUD-RAPIER-SK-10: README thread/platform matrix transfers | FAIL | Desktop only initially; thread modes tested separately; experimental thread packaging rejected. |
| AUD-RAPIER-SK-11: current checkout is implementation-ready | BLOCKED | Acquire v0.35.2 separately, set exact engine, and establish safe remotes. |
| AUD-RAPIER-SK-12: old records are current | BLOCKED at audit time | This refreshed report, workbook, decisions, blockers, and lock resolve the stale planning record. |

No material critic finding was rejected. Two recommendations were sequenced rather than collapsed: minimal custom-JSON builds run before the intended non-API feature matrix, and 3D compatibility is tested in P7-G0 even though 3D product scope remains optional.

## Final gate statement

**PLANNING CLOSED; RAPIER2D IMPLEMENTATION COMPLETE; STABLE PROMOTION BLOCKED.** The historical unchanged-source failure and bounded remediation remain retained. Every local automated Rapier2D gate passes on Windows and Linux. Public source hosting is authorized, but do not claim published stable Redot support or create a tag/release until downstream confirmation/waiver, public pinned CI, and explicit stable-release authorization are retained.

The source-of-truth workbook in this folder records the evaluated sources, decisions, milestones, QA evidence, and risks.
