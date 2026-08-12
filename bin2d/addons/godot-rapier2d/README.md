# Redot Rapier Physics 2D

Rapier2D is an opt-in 2D physics backend for Redot 26.2, built from Godot Rapier Physics 0.35.2 and Rapier 0.35.1. This package preserves the upstream addon path `addons/godot-rapier2d` and includes the full desktop feature profile: standard PhysicsServer2D behavior, custom Rapier nodes, fluids, state serialization, parallel solver support, and editor class documentation.

Each supported platform has distinct editor, debug-export, and release-export native libraries. Generated class documentation is present only in the editor library, so exported games do not embed the editor-only documentation registration feature.

## Install

1. Extract the package into the root of a Redot project so this file is at `addons/godot-rapier2d/README.md`.
2. Open the project with Redot 26.2.
3. Set **Project Settings > Physics > 2D > Physics Engine** to `Rapier2D`.
4. Restart the editor after changing the backend.

Installing the addon does not change an existing project's backend. Projects continue using their configured/default PhysicsServer2D until `Rapier2D` is selected explicitly.

Rapier's point queries honor a collision object's `input_pickable` state by default through `physics/rapier/queries/point_query_honors_pickable`. Set `input_pickable = true` for bodies or areas that a point query should return, or explicitly change that project setting if the project needs different behavior.

## Supported targets

- Windows x86-64
- Linux x86-64
- Redot 26.2 stable, compatible API 4.5.2, single precision

This build is certified for that exact Redot release. A different Redot release requires a separately built and validated plugin version.

## Licenses

The upstream plugin license is in `LICENSE`. Upstream notices are in `THIRDPARTY.txt`. The exact Windows/Linux feature-graph notices, full dependency license texts, and MPL-2.0 source-availability locations are in `THIRDPARTY-REDOT.txt`; the MPL-2.0 license is also provided separately in `LICENSE-MPL-2.0.txt`.
