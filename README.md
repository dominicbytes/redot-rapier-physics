# Redot Rapier Physics

Implementation workspace for the Redot 26.2 port of Godot Rapier Physics (program priority 7).

## Current state

- Preflight: complete as of 2026-08-10
- Planning: owner-approved and closed on 2026-08-11
- Implementation: the Rapier2D `0.35.2-redot.1` source candidate is complete and all local automated Windows/Linux gates pass; stable release remains blocked on the retained downstream-project/waiver decision, public CI, and explicit release authorization
- MS-022 foundation: PASS locally; the infrastructure snapshot, exact engine/API lock, two-addon mapping, Rust adapter, and Windows/Linux matrix are adopted and tested
- P7-G0 result: unchanged `v0.35.2` remains a retained FAIL at `_get_space_state` return nullability; the owner-authorized downstream-only `redot-compat` selector passes minimal 2D/3D debug and release compilation
- Rapier2D result: Windows and Linux editor/debug/release builds, Clippy, 76 Rust unit tests, Redot unit/feature scenes, and the 39-scene regression suite pass; each platform reports 208/210 declared monitors, two inherited expected CCD failures, six improvements, and no unexplained engine/script errors
- Package result: deterministic 58-file archive `redot-rapier-physics-2d-0.35.2-redot.1.zip`, SHA-256 `af8ec56c054981c3c699f166efd91ae1685fda18a87d67762603e609d984b258`; clean selected/default installs and official-template debug/release exports run successfully on both required platforms
- Determinism/performance/legal result: six lockstep replays are byte-identical across Windows/Linux; both platform performance guardrails pass; exact-feature notices and an SPDX 2.3 SBOM cover 87 resolved packages
- Platform status: Windows x86-64 and Linux x86-64 pass the complete local automated candidate matrix; a public run of the pinned workflow remains a promotion gate
- Upstream source target: Godot Rapier Physics `v0.35.2` at `172c66f5a88bf1164c2b8cf2d775ed889edefd75`, verified on 2026-08-12 as the latest stable plugin release
- Release-line pin: the owner fixed `v0.35.2` for this candidate; a newer upstream version is evaluated in a later planned update instead of reopening this release line
- Physics dependency lock: stable `rapier2d` and `rapier3d` `0.35.1`; the selected plugin lock matches the latest stable Rapier tag as of 2026-08-12
- Source repository: public fork `dominicbytes/godot-rapier-physics`, branch `redot-26.2`, based on exact upstream `v0.35.2`
- Rust compatibility prerequisite: `dominicbytes/redot-rust` at `18ad5c538c452b8640420366794354e3ed48f205`
- Redot target: Redot 26.2 stable, compatible Godot API 4.5.2, single precision
- Redot support policy: each plugin release certifies one exact Redot engine/API identity; the first planned release targets Redot 26.2/API 4.5.2, and later Redot versions require separately validated downstream tags
- Goal: add explicit Rapier alternatives without replacing Redot's default physics backends
- Product structure: one source repository with two addon slots; Rapier2D releases first, and Rapier3D ships only if it adds a material user-facing capability beyond Redot Jolt
- Package identity: publish `Redot Rapier Physics 2D` and, only after approval, `Redot Rapier Physics 3D`; use artifact slugs `redot-rapier-physics-2d` and `redot-rapier-physics-3d` while preserving `addons/godot-rapier2d` and `addons/godot-rapier3d` internally
- Versioning: one lockstep `v<upstream-version>-redot.<revision>` tag, beginning with `v0.35.2-redot.1`; Rapier2D releases alone until Rapier3D qualifies, then both public packages advance together
- Rollback boundary: rollback/replay is useful supporting value but cannot justify Rapier3D alone; a rollback-only result becomes a separate future plugin candidate
- Required foundation: `../redot-porting-infrastructure`, adapted at this repository root for Rust/Cargo and two addon packages
- Rapier2D release policy: full applicable feature parity with the pinned upstream 2D plugin; no intentional feature trickle after the first public release
- First-release platforms: Windows x86-64 and Linux x86-64; macOS and other targets are deferred variants
- Determinism guarantee: exact Windows/Linux replay-hash equality for a pinned single-threaded deterministic profile; parallel builds are tested separately without that claim
- Performance policy: use a release-blocking guardrail for crashes, leaks, unbounded growth, instability, and material unexplained regressions; do not require Rapier2D to beat Redot's default backend
- Distribution: publish through both GitHub Releases and the Redot Asset Library. GitHub is the canonical release, attestation, and support record; each Asset Library entry uses an immutable package-only commit from the same repository and must match the corresponding GitHub asset's installed-file manifest exactly
- Installable contents: keep each dimension package lean with only the runtime addon, README, and complete legal notices; publish examples, parity fixtures, and test projects as separate GitHub release assets
- Release posture: publish no public beta or release candidate; after every required gate passes, make the first public GitHub package a stable release and submit only that stable payload to the Redot Asset Library
- Private stable validation: before publication, retain real downstream install, backend-selection, representative runtime, export, and exported-release launch confirmation for the exact candidate package on both Windows and Linux; an explicit owner waiver is allowed only when a suitable downstream tester or project is unavailable and never bypasses automated gates
- Maintenance cadence: monitor every official upstream stable plugin and Rapier crate release and begin evaluation promptly, but promise no fixed publication deadline; publish an update only after the complete applicable compatibility and release matrix passes, and always identify the currently evaluated and pinned stable versions
- Support window: provide routine maintenance only for the newest published Redot release line; older plugin lines remain downloadable and documented but receive no routine fixes
- Routine release rhythm: open a plugin update cycle for each planned stable Redot release, expected roughly quarterly; queue routine Rapier/plugin dependency adoption and accepted repository work for that cycle, then publish only after the full gates pass
- Maintainer intake: the owner reviews pull requests and issues raised on the repository between Redot release cycles and records their disposition; review does not itself promise acceptance, response time, or an immediate release
- Emergency patch exception: permit an out-of-cycle release on the current supported line only for a confirmed security defect, data-loss defect, or release-blocking crash; keep the change narrowly scoped, run the full applicable release gates, and exclude features and routine dependency upgrades

The unchanged-source compatibility gate identified one bounded Redot/gdext nullability mismatch. The approved remediation keeps the exact custom API JSON through dependency feature `godot/api-custom-json`, adds no Rapier top-level Godot API feature, and selects only the existing nullable return implementation. The full local Windows/Linux implementation and release-candidate matrix now passes. The owner authorized the public fork and source push on 2026-08-12; no version tag, GitHub Release, downloadable asset, or Asset Library submission is authorized yet.

See `docs/gamedev/rapier2d-parity-ledger.md`, `docs/gamedev/evidence/rapier2d-desktop-package-validation.json`, `UPSTREAM_LOCK.md`, and `BLOCKERS.md`.
