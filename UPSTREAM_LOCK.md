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
| Downstream source baseline | Branch `redot-26.2` began at exact upstream `v0.35.2` commit `172c66f5a88bf1164c2b8cf2d775ed889edefd75`; the owner authorized its public source commit and push on 2026-08-12 |
| Downstream fork | https://github.com/dominicbytes/godot-rapier-physics |
| Clean implementation probe checkout | `plugins/build/redot-rapier-physics-v0.35.2`; detached exact tag, upstream-only remote |
| Complete tracked payload | 637 files / 79,162,226 bytes; canonical manifest SHA-256 `7e150baf518b72e1b9d40657035be0932e6a3098d666cfedf8bfc93749907e3b` |
| Manifest/lock distinction | `godot = "0.5.4"` is the manifest floor; the v0.35.2 lock resolves the Godot Rust family to 0.5.5 |
| Rapier / Salva lock | crates.io Rapier 0.35.1 / Salva 0.10.0 with checksums; no git sources in the v0.35.2 lock |
| Rapier crate checksums | `rapier2d 0.35.1`: `74bfd393193e08a812ba0c83c7c844dff29979fd30f96de2854cdea507350065`; `rapier3d 0.35.1`: `e1c797fd96e34ae075c7b849741f89968ebedb86b584023420d68a1993bdc5cc` |
| Shared compatibility repository | https://github.com/dominicbytes/redot-rust |
| Compatibility repository pin | `18ad5c538c452b8640420366794354e3ed48f205` (pin commit; no tag/release exists) |
| Required porting foundation | `../redot-porting-infrastructure` |
| Porting foundation identity | Ordered 31-file source manifest SHA-256 `ec5f2e8fe2fe65b94a17d577043aad16b70652bf23a09930e34001710b2ddf54`; generated/cache/binary exclusions are recorded in the snapshot JSON |
| Porting foundation adaptation | Retain Redot bootstrap/API validation/evidence/packaging/desktop CI/release contracts; replace C++/SCons/`redot-cpp` compilation with redot-rust/Cargo and extend metadata to two addons |
| gdext pin | `637cef73172bba23850131acd8583b0c72ebf0c7` (0.5.5 line) |
| Rust toolchain | 1.94.0 |
| Redot engine | 26.2 stable at `4f5b14abade2239104847d03d8f9056e4467cfcd` |
| Compatible API | Godot API 4.5.2, single precision |
| API JSON SHA-256 | `177E7796166929B2193C9CCE2FD32F59601A0147D0D1E7FE904B94E8F69F6577` |
| Interface header SHA-256 | `4CD695E86B92E2BF4E60BBE19CE137FAF41205DA1CF94F29E069AFEC0F7BF320` |
| Required base API contract | Rapier `single-dim2` or `single-dim3`, plus dependency `godot/api-custom-json`; no Rapier top-level `api-*` feature; non-API feature profiles are tested separately |
| Authorized compatibility delta | Empty `redot-compat` feature plus one cfg selector in each existing 2D/3D nullable `_get_space_state` branch; no JSON mutation and no forwarded Godot API feature |
| Downstream package version | `0.35.2-redot.1`; Cargo manifest and lock agree |
| Local deterministic candidate | 58-file `redot-rapier-physics-2d-0.35.2-redot.1.zip`; SHA-256 `af8ec56c054981c3c699f166efd91ae1685fda18a87d67762603e609d984b258`; byte-identical repeat build |
| Current downstream Cargo.lock SHA-256 | `9c8d4ef7866aaf0261dbc3b83b2f7c09db7e50919d91388c49e113c915b87c88` |
| Registry lock preservation | Unrelated registry packages remain at upstream-locked versions, including `num-integer 0.1.46`; the only dependency-source substitution is the recorded gdext pin |
| Rapier2D release scope | Full applicable feature parity with the pinned upstream 2D plugin; every capability requires parity proof, technical not-applicable evidence, or explicit owner waiver |
| First-release platform matrix | Windows x86-64 and Linux x86-64 required; macOS, web, mobile, other architectures, and double precision deferred |
| Determinism release contract | Pinned single-threaded Rapier2D profile must produce identical canonical replay hashes on Windows x86-64 and Linux x86-64; parallel profile tested separately without a cross-platform byte-equality claim |
| Proven floor | v0.8.40, unchanged source, 2D single precision only, Windows debug/release runtime 9/9 |
| License | upstream MIT plus exact-feature dependency notices and MPL-2.0 source-availability obligation for the patched gdext fork |
| Downstream branch | `redot-26.2` |
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

This remains an implementation input lock, not a stable-release authorization. The owner fixed `v0.35.2` as the input for this release line and authorized publishing the source fork on 2026-08-12. Unchanged Rapier `v0.35.2` failed at the shared `_get_space_state` nullability boundary and remains preserved as historical evidence. The owner-authorized `redot-compat` remediation and the complete local Rapier2D Windows/Linux automated matrix now pass, including parity, deterministic replay, performance guardrails, legal output, deterministic packaging, clean installs, exports, and exported runtimes. Do not float on `main`, select a prerelease, mutate the API JSON, enable a top-level Rapier API feature, create a version tag, or publish a stable package before the external promotion gates in `BLOCKERS.md` are closed.
