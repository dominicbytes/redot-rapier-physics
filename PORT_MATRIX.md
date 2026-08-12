# Redot port matrix

This downstream matrix is intentionally narrower than the upstream plugin and the porting-infrastructure fixture. A target is supported only when its Redot-built artifact, clean install, export, and runtime evidence all pass for the exact engine/API identity in `redot.lock.json`.

| Target | First-release status | Rapier2D local candidate | Rapier3D probe | Required build profiles | Local runtime/export gate |
| --- | --- | --- | --- | --- | --- |
| Windows x86_64 | Required | PASS | Compatibility evidence only | editor, template debug, template release | PASS |
| Linux x86_64 | Required | PASS | Compatibility evidence only | editor, template debug, template release | PASS |
| macOS universal | Deferred | Not claimed | Not claimed | None | None |

`PASS` describes the unpublished local `0.35.2-redot.1` candidate, not public support. Public pinned CI and the remaining promotion gates still apply. Web, mobile, other architectures, and double precision are deferred and are not implied by a desktop result. Rapier3D remains unpublished unless its separate Redot Jolt added-capability gate passes.
