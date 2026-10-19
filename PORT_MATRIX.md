# Redot port matrix

The `0.35.2-redot.2` candidate targets exactly Redot 26.3 stable (`85e520394`). A target is supported only after its builds, clean installation, export and runtime gates pass for the engine identity in `redot.lock.json`. The 26.2 binding ABI is a generation input, not a second certified engine (ADR-0317).

| Target | 26.3 requirement | Rapier2D certification | Rapier3D | Required build profiles | Runtime/export gate |
| --- | --- | --- | --- | --- | --- |
| Windows x86_64 | Required | Pending hosted CI | Not a product | editor, template debug, template release | Pending hosted CI |
| Linux x86_64 | Required | Pending hosted CI | Not a product | editor, template debug, template release | Pending hosted CI |
| macOS universal | Deferred | Not claimed | Not claimed | None | None |

No historical 26.2 PASS carries into this line. Windows local compatibility checks inform qualification but do not replace hosted CI or the remaining promotion gates. Web, mobile, other architectures and double precision remain deferred. Rapier3D remains unpublished unless its separate Redot Jolt added-capability gate passes. New Struct values are outside the binding capability subset.
