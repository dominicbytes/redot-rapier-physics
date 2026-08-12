# Architecture decisions

## ADR-0007: Keep Rapier additive

- Date: 2026-08-09
- Status: accepted
- Context: Redot already has default 2D and 3D physics backends, including Jolt for 3D.
- Decision: register Rapier2D and any approved Rapier3D support as explicit alternatives. Untouched projects must retain their existing backend.
- Consequences: every activation test needs a default-backend control and an explicit Rapier-selection assertion.

## ADR-0017: Pin the shared Rust/API prerequisite

- Date: 2026-08-10
- Status: accepted
- Decision: use `dominicbytes/redot-rust` commit `18ad5c538c452b8640420366794354e3ed48f205`, gdext commit `637cef73172bba23850131acd8583b0c72ebf0c7`, Rust 1.94.0, and the recorded Redot 26.2 API artifacts.
- Evidence: public three-platform compatibility-layer CI and exact local API hashes.
- Consequences: `main` is not an acceptable dependency identity; the repository has no release or tag yet.

## ADR-0027: Select Rapier v0.35.2 conditionally

- Date: 2026-08-10
- Status: accepted for planning; blocked for port edits
- Decision: target tag `v0.35.2` at commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75` because it removes the incompatible `godot::sys::is_initialized()` call and its lock resolves the Godot Rust family to 0.5.5.
- Qualification: Cargo.toml's `godot = "0.5.4"` is a semver floor; the committed lock selects 0.5.5.
- Consequences: unchanged source must pass the P7-G0 compatibility probe before any port-specific patch is considered. `v0.8.40` is retained only as a proven 2D single-precision compatibility floor.

## ADR-0037: Let the exact API JSON drive signatures

- Date: 2026-08-10
- Status: accepted
- Decision: use Rapier top-level `single-dim2` or `single-dim3` as the base, and enable dependency feature `godot/api-custom-json` through an external consumer harness. Add `register-docs`, `serde-serialize`, and solver `parallel` only as explicit non-API test profiles.
- Rejected: Rapier top-level `api-4-5`, which selects signatures that do not match the exact Redot JSON; Rapier top-level `api-custom`, which selects newer branches and rejects Redot product major 26.
- Consequences: the gate must capture actual Cargo metadata and fingerprints rather than trusting a declared feature label.

## ADR-0047: Prove 2D first and gate 3D by value

- Date: 2026-08-10
- Status: accepted
- Decision: after the shared 2D/3D compatibility gate, deliver the 2D vertical slice and feature acceptance first. Continue 3D product work only if a parity/value comparison against Redot Jolt identifies an approved benefit.
- Consequences: 3D compatibility evidence is mandatory, but compatibility alone does not authorize a full 3D product scope.

## ADR-0057: Keep one repository and publish two installables

- Date: 2026-08-10
- Status: accepted
- Decision: maintain one shared source repository and publish Rapier2D and Rapier3D as independently installable addons. Release the 2D addon first; the 3D addon remains behind its value/parity gate.
- Rationale: separate packages let users install only the dimension they need and isolate dimension-specific binaries, manifests, and failures without creating two drifting source forks.
- Consequences: builds, manifests, archives, and clean-install tests are dimension-specific; CI must also prove that both addons can coexist in one project without duplicate registration. Public package names remain a later naming decision.

## ADR-0067: Adopt the Redot porting infrastructure as the repository foundation

- Date: 2026-08-10
- Status: accepted
- Decision: use `../redot-porting-infrastructure` as the required foundation beside the Rapier repository. Preserve its Redot acquisition, API identity validation, evidence, deterministic packaging, desktop matrix, and tagged-release contracts.
- Adaptation boundary: replace the fixture's C++/SCons/`redot-cpp` compile adapter with the pinned redot-rust/Cargo consumer and build flow, and extend the single-addon metadata contract to describe two installables under one shared upstream and toolchain lock.
- Rejected: copying the fixture wholesale with `redot-cpp`, maintaining a second infrastructure repository inside the plugin repository, or building an unrelated release pipeline.
- Consequences: the local infrastructure snapshot needs an immutable provenance record before implementation because the supplied directory is not itself a Git checkout. Rapier release gates must also add release-export runtime proof beyond the fixture's editor/debug smoke.

## ADR-0077: Make full applicable Rapier2D parity a first-release gate

- Date: 2026-08-10
- Status: accepted
- Decision: the first public Rapier2D package must implement and verify every 2D capability exposed by the pinned upstream plugin that is applicable to Redot 26.2. Do not intentionally defer fluids, state serialization/restore, nodes/resources, physics-server behavior, queries, joints, settings, documentation, or other upstream 2D features to later feature releases.
- Parity rule: every inventoried upstream 2D capability must finish as `Parity PASS`, `Not applicable` with technical evidence, or an explicit owner-approved release waiver. A missing or degraded capability is otherwise a release blocker.
- Rationale: a complete initial package avoids a long feature trickle and gives users a credible replacement for the original plugin's 2D offering.
- Consequences: the 2D parity matrix and acceptance suite are release-critical. Compatibility alone, a minimal backend slice, or fluids/serialization previews cannot qualify as the public Rapier2D release.

## ADR-0087: Require Windows and Linux for the first release

- Date: 2026-08-10
- Status: accepted
- Decision: the first public Rapier2D release supports Windows x86-64 and Linux x86-64. Both platforms are mandatory release gates and must carry the complete approved Rapier2D feature surface.
- Deferred: macOS, web, Android, iOS, other architectures, and double precision are separate later platform variants with their own evidence gates.
- Rationale: concentrating the initial platform matrix keeps the full-feature parity goal achievable without claiming or maintaining an unrequested macOS package.
- Consequences: adapt the porting infrastructure's default desktop contract so Windows and Linux are required and macOS is explicitly disabled/deferred. Documentation, manifests, archives, CI, and release metadata must make the platform boundary unambiguous.

## ADR-0097: Require exact cross-platform hashes for the deterministic profile

- Date: 2026-08-10
- Status: accepted
- Decision: a designated single-threaded Rapier2D deterministic profile must produce identical canonical replay hashes on Windows x86-64 and Linux x86-64 before release.
- Profile boundary: pin the source, Rust toolchain, dependency graph, Redot/API identity, precision, Cargo features, compiler settings, seed, initial state, input stream, timestep, frame count, and stable state encoding. Disable solver parallelism and Redot separate-thread execution for this profile.
- Parallel profile: the normal parallel build remains release-tested for physics correctness, stability, export, and repeatability on each platform, but it does not claim byte-identical Windows/Linux replay hashes without separate proof.
- Failure rule: any unexplained same-platform or cross-platform deterministic-profile hash divergence is release-blocking.
- Consequences: CI must retain the canonical inputs, environment metadata, checkpoint/final hashes, and divergence diagnostics as release evidence.

## ADR-0107: Use a performance guardrail, not an improvement mandate

- Date: 2026-08-10
- Status: accepted
- Decision: Rapier2D is not required to match or beat Redot's default backend in every benchmark. Release is blocked by crashes or hangs, physics correctness or stability failures, memory leaks or unbounded growth, and material unexplained frame-time or memory regressions against frozen baselines for identical small, medium, high-body-count, and fluid workloads.
- Threshold protocol: capture the baseline measurements first, then freeze the workload definitions, environment, warm-up, sample counts, aggregation method, and numerical regression thresholds before comparing a release candidate. Publish the raw Rapier2D and Redot-default results with the decision evidence.
- Rationale: this prevents arbitrary pre-measurement targets and avoids treating benchmark wins as a product requirement while still rejecting pathological or materially degraded behavior.
- Consequences: performance improvements are optional; moving thresholds after a candidate result, hiding workload failures in averages, or shipping an unexplained material regression is prohibited.

## ADR-0117: Ship Rapier3D only when it adds capability beyond Redot Jolt

- Date: 2026-08-10
- Status: accepted
- Decision: Rapier3D may become a public addon only if a frozen comparison demonstrates at least one material, testable user-facing capability that the pinned Redot Jolt backend does not provide.
- Insufficient evidence: compatibility, ordinary parity, an alternate implementation, or benchmark equivalence alone does not authorize a Rapier3D release.
- Gate protocol: identify the proposed differentiator before 3D product implementation, freeze the Jolt and Rapier comparison scenario, demonstrate the capability end to end, document remaining parity gaps and maintenance cost, and obtain owner approval. If no qualifying capability exists, record a no-go and ship Rapier2D without Rapier3D.
- Consequences: the repository can retain the 3D compatibility probe and package schema without promising a 3D product; a speculative or redundant Rapier3D addon is out of scope.

## ADR-0127: Treat rollback as supporting value, not sufficient Rapier3D value

- Date: 2026-08-11
- Status: accepted
- Decision: a documented, end-to-end rollback or deterministic replay workflow is a useful Rapier3D differentiator, but it cannot be the sole reason to publish Rapier3D.
- Failure rule: if rollback/replay is the only material capability Rapier3D adds beyond Redot Jolt, close the Rapier3D product gate as no-go.
- Separate candidate: record a backend-neutral standalone rollback plugin as a possible future project rather than coupling that feature to a redundant 3D physics backend.
- Consequences: the standalone rollback candidate is out of scope for this repository and plan; it receives no implementation tasks, release promise, or shared package surface here.

## ADR-0137: Preserve upstream addon paths behind Redot-branded packages

- Date: 2026-08-11
- Status: accepted
- Decision: retain the upstream internal addon directories `addons/godot-rapier2d` and `addons/godot-rapier3d`.
- Public identity: use Redot-branded archive filenames, release labels, catalog entries, and addon display names. The `godot-rapier*` directory names are an intentional compatibility detail, not the public product name.
- Rationale: preserving the established paths avoids unnecessary resource-path, UID, documentation, fixture, and upstream-sync churn.
- Rejected alternative: renaming the directories to `addons/redot-rapier2d` and `addons/redot-rapier3d` would improve internal branding but create migration work without adding user-facing capability.
- Consequences: packaging and clean-install tests must assert the preserved paths, Redot-branded external identity, and absence of cross-addon path collisions; implementation must not perform a cosmetic mass path rewrite.

## ADR-0147: Use lockstep repository and package versions

- Date: 2026-08-11
- Status: accepted
- Decision: use one repository release version and Git tag for all dimension-specific artifacts published from that release. Once both addons are public, Rapier2D and Rapier3D advance together even when a change affects only one dimension.
- Pre-3D rule: Rapier2D may release alone while Rapier3D remains behind its added-capability gate. Lockstep versioning does not create a placeholder, preview, or implied Rapier3D package.
- Rationale: one version maps unambiguously to one source commit, Cargo lock, Redot/API identity, evidence set, and supported artifact matrix.
- Rejected alternative: independent 2D and 3D version streams would avoid some unchanged-package bumps but multiply source, dependency, evidence, and support combinations.
- Consequences: after Rapier3D earns its first public release, any release promotion rebuilds, retests, versions, and publishes both qualified addon packages from the same tag.

## ADR-0157: Derive downstream tags from the pinned upstream version

- Date: 2026-08-11
- Status: accepted
- Decision: use Git tags in the form `v<upstream-version>-redot.<downstream-revision>`. The first planned release from upstream Rapier `v0.35.2` is `v0.35.2-redot.1`.
- Increment rule: downstream source, build, packaging, or release fixes that retain upstream `v0.35.2` advance to `redot.2`, `redot.3`, and so on. Adopting a different upstream version resets the downstream revision to `redot.1`.
- Artifact rule: omit the leading `v` inside package metadata where a semantic version is required, but require every archive, manifest, checksum, attestation, and release record to map to the exact Git tag.
- Rationale: the label exposes both the upstream source baseline and the downstream port revision without maintaining a second unrelated product version.
- Tradeoff: the suffix is SemVer prerelease syntax and public numbering remains tied to upstream rather than presenting the port as an independent `1.0.0` product.
- Consequences: release validation must reject inconsistent upstream bases, non-monotonic Redot revisions, or artifacts that cannot be traced to the declared tag.

## ADR-0167: Certify each release against one exact Redot identity

- Date: 2026-08-11
- Status: accepted
- Decision: each downstream plugin release certifies exactly one pinned Redot engine release/commit and matching API identity. The first planned `v0.35.2-redot.1` release targets Redot 26.2 stable, compatible API 4.5.2, and the recorded interface/API hashes.
- Platform rule: Windows x86-64 and Linux x86-64 packages may share that certified Redot identity, but they must both be built and tested against it.
- Upgrade rule: supporting another Redot version requires a new downstream tag and the complete required compatibility, package, export, runtime, determinism, and release matrix. Technical loadability on an unlisted version is not a support claim.
- Artifact rule: manifests, release notes, checksums, attestations, and support records must name the single certified Redot/API identity for their tag.
- Rationale: one-to-one certification keeps ABI/API evidence auditable and prevents a broad compatibility label from hiding engine-version differences.
- Rejected alternative: advertise a Redot version range or infer support for newer/older releases from one successful build.
- Consequences: release validation must reject missing, multiple, or mismatched Redot identities and must not carry compatibility evidence forward to another engine release.

## ADR-0177: Name the public installables Redot Rapier Physics 2D and 3D

- Date: 2026-08-11
- Status: accepted
- Display names: use `Redot Rapier Physics 2D` and `Redot Rapier Physics 3D` in public manifests, release assets, catalogs, documentation, and support records.
- Artifact slugs: use `redot-rapier-physics-2d` and `redot-rapier-physics-3d` as the stable archive/package slug prefixes.
- Internal-path rule: retain `addons/godot-rapier2d` and `addons/godot-rapier3d`; the public naming decision does not authorize a directory rename.
- Rapier3D rule: reserving its name and slug does not create a package, preview, or release promise. The 3D artifact remains absent until the added-capability gate passes.
- Rationale: explicit dimension-specific Redot names are searchable, unambiguous, and consistent across the shared repository without obscuring which installable a user receives.
- Rejected alternative: shorter but less consistent `Rapier2D for Redot` / `Rapier3D for Redot` labels or different names across archives, manifests, and catalogs.
- Consequences: packaging tests must reject identity drift, a mismatched dimension, changed internal paths, or any pre-approval Rapier3D publication.

## ADR-0187: Publish through GitHub Releases and the Redot Asset Library

- Date: 2026-08-11
- Status: accepted
- Decision: distribute every approved public package through both GitHub Releases and the Redot Asset Library. GitHub Releases is the canonical version, release-notes, checksum, attestation, evidence, and support record.
- Asset Library constraint: Redot's catalog computes a download from a repository URL and exact commit rather than consuming an attached GitHub release asset. Use a package-only immutable commit in this same repository for each approved dimension and exact Redot version. Create one Asset Library entry per installable; do not publish a Rapier3D entry before its product gate passes.
- Equality rule: stage each package once. The catalog commit and GitHub asset may use different outer archive containers, but their installed addon file paths and per-file SHA-256 manifest must match exactly. Reject an independent rebuild, a mutable branch reference, extra dimension payloads, or any manifest drift.
- Version rule: the catalog entry uses the same public name, package version, certified Redot version, license, and support links as the GitHub release. Package commits are mirrors of the lockstep release, not another version stream.
- Rationale: dual publication gives direct, attestable downloads and in-editor discoverability without maintaining separate source repositories or separately built binaries.
- Consequences: release promotion publishes and validates GitHub first, then submits the exact package mirror to manual Asset Library review. The addon folder must carry its own README and license, and a new Redot support identity requires a new catalog entry.

## ADR-0197: Freeze the latest stable plugin and both Rapier crates

- Date: 2026-08-11
- Status: accepted
- Current result: the official latest stable Godot Rapier Physics release is `v0.35.2` at `172c66f5a88bf1164c2b8cf2d775ed889edefd75`. Its committed lock selects stable `rapier2d 0.35.1` and `rapier3d 0.35.1`, which crates.io reports as the maximum stable version of both crates as of 2026-08-11.
- Decision: require the source lock to use the latest stable plugin release and the latest stable Rapier crate release for both dimensions. Pin the tag, full commit, committed Cargo lock, registry checksums, and actual resolved graph; never use mutable `main`, a beta/alpha, or floating semver resolution as the release identity.
- Freshness gate: immediately before P7-G0, query the official plugin `releases/latest` record and the crates.io maximum-stable metadata for both `rapier2d` and `rapier3d`. If any stable version changed, refresh preflight, the lock, parity inventory, and compatibility inputs before source edits.
- Mismatch rule: if the newest stable plugin does not lock the newest stable Rapier crates, stop the source freeze and open an explicit dependency-upgrade compatibility gate. Do not silently bump only one crate or claim that the plugin version proves the physics version.
- Rationale: this preserves the user's latest-stable requirement without trading away reproducibility or hiding the distinct plugin and physics-engine version numbers.
- Consequences: the current first planned downstream tag remains `v0.35.2-redot.1`; any newer upstream stable adopted before implementation resets the downstream suffix to `redot.1` for that new upstream version.

## ADR-0207: Keep each installable lean and publish examples separately

- Date: 2026-08-11
- Status: accepted
- Decision: each dimension-specific installable contains only the runtime addon at its preserved internal path plus the addon's README and complete upstream/dependency/MPL legal notices. Examples, parity fixtures, and test projects are separate companion assets on the matching GitHub release.
- Catalog rule: Redot Asset Library package commits contain the same lean installable payload and required root metadata; they do not bundle examples, parity fixtures, test projects, repository development files, or the other dimension.
- Equality rule: the canonical GitHub installable and matching catalog package commit retain identical installed-file paths and per-file SHA-256 values. Companion assets are versioned by the same release tag but are outside that equality comparison.
- Rationale: users receive a clean project install and smaller catalog download while developers retain complete, inspectable examples and validation material.
- Tradeoff: hands-on examples require one additional GitHub download and are not immediately visible after an Asset Library install.
- Consequences: packaging tests must reject development-only files in installables, release notes must link the matching companion assets, and every companion asset must identify the same version, Redot identity, and dimension as its canonical package.

## ADR-0217: Publish the first public package directly as stable

- Date: 2026-08-11
- Status: accepted
- Decision: publish no public beta, preview, or release-candidate package. After all compatibility, parity, Windows/Linux, determinism, performance, packaging, legal, clean-install, export, and runtime gates pass, publish the first public GitHub package as a non-prerelease stable release and submit that same stable payload to the Redot Asset Library.
- Internal validation rule: CI and local workflows may produce unpublished candidate artifacts for testing and approval. They are evidence inputs, not supported releases, and must not be attached to a public GitHub release or submitted to the catalog.
- Version rule: retain the approved `v<upstream-version>-redot.<revision>` tag scheme, beginning with `v0.35.2-redot.1`, and mark the GitHub release as non-prerelease. Strict SemVer tooling can interpret the hyphenated suffix as prerelease syntax; the downstream support status is defined by the stable GitHub release record and catalog publication.
- Rationale: one public support boundary avoids prerelease-user confusion and aligns the first public package with the full-feature, release-gated quality bar.
- Tradeoff: the project receives less public integration feedback before stable publication, so pre-publication validation must be correspondingly strong.
- Consequences: release automation must reject public prerelease flags, beta/RC assets, and early catalog commits; release notes must not describe the first public package as experimental or incomplete.

## ADR-0227: Require private downstream confirmation on both release platforms

- Date: 2026-08-11
- Status: accepted
- Decision: before the first stable publication, validate the exact staged candidate package in a real downstream project on both Windows x86-64 and Linux x86-64 after all automated gates pass. Retain evidence of clean installation, explicit Rapier backend selection, representative collision or query behavior, project export, exported-release launch, and review of errors and warnings.
- Evidence identity: each confirmation records the downstream project or fixture, candidate package SHA-256 and release tag, exact Redot engine/API identity, operating system, commands or actions performed, observed results, and tester. One tester may cover both platforms or separate testers may supply the per-platform records, but the tested package bytes must be identical to the release candidate.
- Waiver rule: only the absence of a suitable downstream tester or project may be waived. The owner must retain an explicit approval naming the unavailable validation, reason, and residual risk. A waiver cannot bypass repository CI, compatibility, parity, platform, determinism, performance, packaging, legal, export, runtime, or payload-equality gates.
- Rationale: direct-to-stable publication has no public RC feedback period, so real downstream use on both supported platforms provides a final check for installation, environment, and project-integration assumptions that repository fixtures can miss.
- Tradeoff: the gate adds tester coordination and can delay publication, but it keeps the stable label aligned with the stronger prepublication evidence boundary.
- Consequences: a failed downstream confirmation keeps the candidate unpublished until the defect is fixed and both affected evidence paths are rerun; release records must link the retained confirmations or the narrowly scoped owner waiver.

## ADR-0237: Evaluate upstream stable releases promptly without a publication deadline

- Date: 2026-08-11
- Status: accepted
- Decision: monitor every official stable Godot Rapier Physics plugin release and stable `rapier2d`/`rapier3d` crate release. Begin a recorded compatibility, dependency, parity-impact, and release-scope evaluation promptly after discovery, but make no promise to publish the corresponding Redot update within a fixed number of days.
- Publication rule: adopt and publish a newer stable source only after the complete applicable compatibility, Windows/Linux, parity, determinism, performance, packaging, legal, downstream-validation, and distribution gates pass. A newer upstream version never authorizes a partial, unverified, or deadline-driven Redot release.
- Transparency rule: project status, release notes, and maintenance records identify the newest stable versions evaluated, the versions currently pinned, any known lag, and the blocking gate or explicit disposition. If the newest plugin does not lock the newest stable Rapier crates, retain the existing dependency-upgrade compatibility gate rather than silently floating either dimension.
- Rationale: prompt evaluation preserves awareness of upstream fixes and compatibility changes, while a gate-driven publication schedule protects the stable support promise and avoids converting freshness into pressure to bypass evidence.
- Tradeoff: the Redot port may temporarily trail upstream and cannot advertise a guaranteed update turnaround.
- Consequences: maintenance automation or checklists must create an auditable evaluation record for each stable release; publication timing remains an outcome of the required evidence, not a calendar deadline.

## ADR-0247: Maintain the newest Redot line and align routine updates with Redot releases

- Date: 2026-08-11
- Status: accepted
- Support-window decision: after a newer Redot-specific plugin release is published, only that newest line receives routine maintenance. Older release artifacts and their exact compatibility records remain available, but ordinary bug fixes, dependency updates, and feature work are not backported to them.
- Routine-release decision: open a plugin update cycle only for a planned stable Redot release, expected roughly quarterly. Stable upstream plugin and Rapier releases discovered between cycles remain monitored and recorded, then are considered with accepted repository work when the next Redot cycle opens. The full applicable gate matrix, not the calendar, still determines publication.
- Maintainer-intake decision: the owner checks pull requests and issues raised on the repository between release cycles and records a disposition such as accept, reject, defer to the next Redot cycle, duplicate, or needs evidence. Review does not promise acceptance, a response-time service level, or an immediate package update.
- Rationale: one routinely maintained line matches the one-exact-Redot-identity release model and keeps Windows/Linux, parity, determinism, packaging, and support work sustainable for a single maintainer. Redot-aligned cycles make compatibility work predictable without floating dependencies.
- Tradeoff: users pinned to older Redot releases will not receive ordinary fixes, and upstream improvements or community contributions may wait for the next Redot cycle even after technical review.
- Emergency exception: ADR-0257 permits a narrowly scoped out-of-cycle patch on the current supported line for confirmed security, data-loss, or release-blocking crash defects.
- Consequences: release/status documentation must name the current routinely supported line; issue and pull-request triage must identify the target Redot cycle or non-release disposition; no routine update may silently create a second maintained line.

## ADR-0257: Permit narrowly scoped emergency patches between Redot releases

- Date: 2026-08-11
- Status: accepted
- Decision: a confirmed security defect, data-loss defect, or release-blocking crash may trigger an out-of-cycle patch on the current routinely supported Redot-specific line. Ordinary bugs, feature work, and routine dependency adoption wait for the next planned Redot release cycle.
- Scope rule: change only what is necessary to remediate the qualifying defect. A dependency change is permitted only when it is required by the remediation; it is not an opportunity to take unrelated upgrades.
- Validation rule: the emergency label waives the quarterly timing rule only. The candidate must pass the complete applicable compatibility, Windows/Linux, parity-regression, determinism, performance, packaging, legal, downstream-validation, and distribution gates before stable publication.
- Release identity: use the normal downstream revision, lockstep artifact, exact-Redot certification, GitHub Release, and Redot Asset Library rules. Do not backport the patch to retired lines as routine support.
- Rationale: waiting as long as a quarter can leave users exposed to a severe defect, while a tightly bounded exception avoids turning ordinary maintenance into continuous release pressure.
- Tradeoff: an emergency patch creates unplanned validation and publication work, but it preserves the stable support promise for defects whose impact outweighs that overhead.
- Consequences: every emergency record must identify the qualifying defect, evidence supporting its classification, exact patch scope, affected supported line, validation results, and excluded unrelated work.

## ADR-0267: Close planning and begin guarded implementation

- Date: 2026-08-11
- Status: accepted
- Decision: accept the recorded destination, product scope, release boundary, quality gates, maintenance policy, and milestone sequence as shared understanding. Close the planning phase and begin implementation with MS-022.
- Guardrail: implementation may freeze inputs, adopt and adapt the porting-infrastructure contract, create the external compatibility harness, and produce evidence. Rapier plugin source or packaging changes remain prohibited until unchanged v0.35.2 passes P7-G0.
- Rationale: the remaining uncertainties are technical gates with explicit failure paths, not unresolved product decisions.
- Consequences: RSK-031 closes; MS-022 becomes active; a failed freshness check or P7-G0 result stops source work without reopening settled product scope.

## ADR-0277: Authorize the bounded Redot nullability selector

- Date: 2026-08-11
- Status: accepted
- Decision: after retaining the unchanged-source failure and exact 637-file source boundary, authorize a downstream-only empty `redot-compat` feature. It may select only the two existing nullable `_get_space_state` implementations, one for 2D and one for 3D. Keep dependency-qualified `godot/api-custom-json`; do not enable Rapier's top-level `api-4-5`, `api-custom`, or another `api-*` feature, and do not mutate the API JSON.
- Evidence: minimal 2D and 3D debug/release builds pass against Redot 26.2/API 4.5.2 and gdext `637cef73172bba23850131acd8583b0c72ebf0c7`. The full Rapier2D profile also passes debug/release compilation and Clippy on Windows; the staged release DLL passes the focused smoke and completes all 39 upstream regression scenes with `STATUS: SUCCESS` (208/210 monitors, two declared expected failures, six improvements).
- Scope boundary: the compatibility result authorizes continued Rapier2D implementation and packaging work only. It does not approve Rapier3D as a product, establish Linux support before CI runs, close the full 2D parity ledger, or waive export, clean-install, determinism, performance, legal, downstream-validation, or publication gates.
- Consequences: RSK-032 closes; MS-022 completes; MS-027 is recorded as an unchanged-source failure resolved by an explicit bounded downstream remediation; MS-037/MS-047 begin. The downstream candidate version is `0.35.2-redot.1`.

## ADR-0287: Lock the release line to v0.35.2 and accept the local Rapier2D candidate

- Date: 2026-08-12
- Status: accepted
- Source decision: fix Godot Rapier Physics `v0.35.2` / `172c66f5a88bf1164c2b8cf2d775ed889edefd75` and its committed Rapier 0.35.1 dependency lock for this release line. A newer upstream release does not reopen or invalidate this candidate; evaluate it in a later planned Redot update. This narrows ADR-0197 and ADR-0237 for the current line while retaining their monitoring policy for future cycles.
- Implementation result: the local `0.35.2-redot.1` Rapier2D candidate passes all automated Windows x86-64 and Linux x86-64 gates: source/addon parity, editor/debug/release builds, Clippy, 76 Rust unit tests, Redot unit and feature scenes, 39 regression scenes, six-run lockstep replay, performance guardrails, exact-feature license/SBOM output, deterministic packaging, selected/default clean installs, and debug/release export launches.
- Artifact identity: the deterministic 58-file archive is `redot-rapier-physics-2d-0.35.2-redot.1.zip`, SHA-256 `af8ec56c054981c3c699f166efd91ae1685fda18a87d67762603e609d984b258`.
- Promotion boundary: at the time of this decision, the local result authorized no external action. ADR-0297 later authorizes the public fork and source push only. Stable promotion still requires retained downstream confirmation or the defined waiver, a public run of the pinned workflow for the exact revision, and explicit authorization for the tag and release channels.
- Rapier3D boundary: no 3D package is approved. Its separate Jolt added-capability gate remains unchanged.

## ADR-0297: Publish the Redot source as a public GitHub fork

- Date: 2026-08-12
- Status: accepted
- Decision: create the public `dominicbytes/godot-rapier-physics` fork of `appsinacup/godot-rapier-physics`, commit the complete Redot implementation and retained evidence, and push it on branch `redot-26.2`.
- Repository boundary: keep `origin` on the `dominicbytes` fork and `upstream` on `appsinacup`; make `redot-26.2` the fork's default branch so visitors and the pinned workflow see the Redot implementation.
- Publication boundary: this authorizes source hosting and public CI only. It does not authorize `v0.35.2-redot.1`, a GitHub Release or attached candidate archive, a package-only Asset Library commit, or an Asset Library submission.
- Hygiene: exclude transient `build/`, Cargo targets, editor caches, Python bytecode, and machine-local paths from the public source commit while retaining the compact validation evidence and legal/SBOM records.
