# Upstream lock: Godot Rapier Physics for Redot

| Field | Value |
|---|---|
| Project | Godot Rapier Physics for Redot |
| Original/current priority | 7 / 7 |
| Authoritative upstream | https://github.com/appsinacup/godot-rapier-physics |
| Conditional source target | tag `v0.35.2`, commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75` |
| Release-line pin policy | Owner-fixed on 2026-08-12: keep `v0.35.2` for this release line; evaluate newer upstream versions in a later planned update rather than reopening the candidate |
| Stable-release freshness | Checked 2026-08-12: the official plugin releases page marks `v0.35.2` latest, and the official Dimforge Rapier tags page lists `v0.35.1` as the newest stable library tag |
| Tag identity | lightweight tag; target commit is unsigned |
| Downstream source baseline | Branch `redot-26.2` began at exact upstream `v0.35.2` commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75` |
| Downstream fork | https://github.com/dominicbytes/redot-rapier-physics |
| Complete tracked payload | 637 files / 79,162,226 bytes; canonical manifest SHA-256 `7e150baf518b72e1b9d40657035be0932e6a3098d666cfedf8bfc93749907e3b` |
| Manifest/lock distinction | `godot = "0.5.4"` is the manifest floor; the v0.35.2 lock resolves the Godot Rust family to 0.5.5 |
| Rapier / Salva lock | crates.io Rapier 0.35.1 / Salva 0.10.0 with checksums; no git sources in the v0.35.2 lock |
| Rapier crate checksums | `rapier2d 0.35.1`: `74bfd393193e08a812ba0c83c7c844dff29979fd30f96de2854cdea507350065`; `rapier3d 0.35.1`: `e1c797fd96e34ae075c7b849741f89968ebedb86b584023420d68a1993bdc5cc` |
| Shared compatibility repository | https://github.com/dominicbytes/redot-rust |
| Compatibility repository pin | `1a7e4d43dd6f77d998e0df4e25724c4c40bc7776` (pin commit; no tag/release exists) |
| Required porting foundation | `../redot-porting-infrastructure` |
| Porting foundation identity | Ordered 31-file source manifest SHA-256 `ec5f2e8fe2fe65b94a17d577043aad16b70652bf23a09930e34001710b2ddf54`; generated/cache/binary exclusions are recorded in the snapshot JSON |
| Porting foundation adaptation | Retain Redot bootstrap/API validation/evidence/packaging/desktop CI/release contracts; replace C++/SCons/`redot-cpp` compilation with redot-rust/Cargo and extend metadata to two addons |
| gdext pin | `637cef73172bba23850131acd8583b0c72ebf0c7` (0.5.5 line) |
| Rust toolchain | 1.94.0 |
| Redot engine | 26.3 stable at `85e5203945af15755dd2f66cb6fdf7545fd88c0b`, output `26.3.stable.official.85e520394` |
| Compatible API | Godot API 4.5.2, single precision |
| Raw engine API JSON SHA-256 | `4c709d5920855dfe7294d01b9899d21aec4e94d3df9fc46f7aa90ad8fff5a38e` |
| Raw engine interface SHA-256 | `558c1f54f5e37afdf259fec29d6eb72da83781afdce48e51a1783942f9cf9895` |
| Binding ABI input | Redot 26.2 stable (`4f5b14abade2239104847d03d8f9056e4467cfcd`), reproduced from checksum-pinned release archives; ADR-0317 |
| Binding API / interface SHA-256 | `177e7796166929b2193c9cce2fd32f59601a0147d0d1e7fe904b94e8f69f6577` / `4cd695e86b92e2bf4e60bbe19ce137faf41205da1cf94f29e069afec0f7bf320` |
| Binding capability limit | New Struct values are unsupported; remove the ABI split only with working engine converters and a Struct-capable binding revision |
| Required base API contract | Rapier `single-dim2` or `single-dim3`, plus dependency `godot/api-custom-json`; no Rapier top-level `api-*` feature; non-API feature profiles are tested separately |
| Authorized compatibility delta | Empty `redot-compat` feature plus one cfg selector in each existing 2D/3D nullable `_get_space_state` branch; no JSON mutation and no forwarded Godot API feature; explicit 26.2 binding-ABI / 26.3 engine split (ADR-0317) |
| Recorded runtime fixes | Each change to an upstream runtime file is listed in `compat/source-deltas/` (ADR-0307); the parity report enumerates them |
| Downstream package version | `0.35.2-redot.2` / `v0.35.2-redot.2`; unpublished-candidate; Cargo manifest and lock agree |
| 26.3 package qualification | Pending hosted builds, determinism, performance, clean-install and export gates |
| Current downstream Cargo.lock SHA-256 | `bfbc48d37f76b718d2e4df3b9c408f8a5d5df8edd5745e82dc8388a09887ac3f` |
| Registry lock preservation | Unrelated registry packages remain at upstream-locked versions, including `num-integer 0.1.46`; the only dependency-source substitution is the recorded gdext pin |
| Rapier2D release scope | Full applicable feature parity with the pinned upstream 2D plugin; every capability requires parity proof, technical not-applicable evidence, or explicit owner waiver |
| First-release platform matrix | Windows x86-64 and Linux x86-64 required; macOS, web, mobile, other architectures, and double precision deferred |
| Determinism release contract | Pinned single-threaded Rapier2D profile must produce identical canonical replay hashes on Windows x86-64 and Linux x86-64; parallel profile tested separately without a cross-platform byte-equality claim |
| Proven floor | v0.8.40, unchanged source, 2D single precision only, Windows debug/release runtime 9/9 |
| License | upstream MIT plus exact-feature dependency notices and MPL-2.0 source-availability obligation for the pinned, unmodified gdext crates |
| Downstream branch | `redot-26.3` |
| Distribution channels | GitHub Releases and separate Redot Asset Library entries for each approved dimension and exact Redot version |
| Asset Library mirror rule | Publish from an immutable package-only commit in this same repository; compare the installed-file path/SHA-256 manifest with the corresponding GitHub release asset and reject any drift or independent rebuild |
| Installable payload | Runtime addon plus README and complete upstream/dependency/MPL notices; examples, parity fixtures, and test projects are separate GitHub companion assets and are excluded from Asset Library payloads |
| Publication posture | Direct to stable after all required gates; no public beta/RC and no prerelease Asset Library entry; unpublished internal candidate artifacts remain permitted for validation |
| Private downstream validation | Stable publication requires retained install, explicit backend selection, representative runtime, export, and exported-release launch evidence for the exact candidate package on both Windows x86-64 and Linux x86-64; an explicit owner waiver is permitted only when no suitable downstream tester/project is available and does not waive automated gates |
| Upstream maintenance cadence | Monitor every official stable plugin and `rapier2d`/`rapier3d` release and begin a recorded evaluation promptly; promise no fixed publication deadline, publish only after the full applicable gates pass, and document the latest evaluated identities plus the versions currently pinned by the Redot port |
| Supported release window | Routine maintenance applies only to the newest published Redot-specific plugin line; older exact-Redot releases remain available and documented but are not routine backport targets |
| Routine publication rhythm | A planned stable Redot release, expected roughly quarterly, opens the next routine plugin update cycle; upstream stable changes and accepted repository work are evaluated for that cycle, but full gates still determine whether and when it publishes |
| Maintainer intake | The owner reviews repository pull requests and issues between Redot cycles and records acceptance, rejection, deferral, duplication, or need for more evidence; review creates no response-time or immediate-release commitment |
| Emergency release exception | A confirmed security defect, data-loss defect, or release-blocking crash may trigger a narrowly scoped out-of-cycle patch on the current supported line only; the full applicable gate matrix remains mandatory, and features or routine dependency upgrades are excluded |

This remains an implementation input lock, not a stable-release authorization. The release line fixes `v0.35.2` as its input. Unchanged Rapier `v0.35.2` failed at the shared `_get_space_state` nullability boundary and remains preserved as historical evidence. The 26.2 automated evidence remains historical. The 26.3 line retains the nullability remediation and now distinguishes the certified engine audit snapshot from the binding input. Its Windows/Linux publication matrix is pending hosted CI and the remaining promotion gates. Do not float on `main`, select a prerelease, mutate the API JSON, enable a top-level Rapier API feature, create a version tag, or publish a stable package before the external promotion gates in `BLOCKERS.md` are closed.
