# Redot Rapier Physics

[![Redot Rapier2D contract](https://github.com/dominicbytes/godot-rapier-physics/actions/workflows/redot-contract.yml/badge.svg?branch=redot-26.2)](https://github.com/dominicbytes/godot-rapier-physics/actions/workflows/redot-contract.yml)

An opt-in Rapier2D physics backend for Redot 26.2, based on [Godot Rapier Physics v0.35.2](https://github.com/appsinacup/godot-rapier-physics/releases/tag/v0.35.2) and Rapier 0.35.1.

> **Release status:** The source candidate is public on the `redot-26.2` branch. No version tag or downloadable package has been published yet.

## Features

The Redot port keeps the full applicable 2D feature set from the pinned upstream plugin:

- Standard `PhysicsServer2D` bodies, shapes, spaces, areas, queries, callbacks, and joints
- Custom Rapier2D nodes and resources
- 2D fluids and fluid effects
- Physics-state serialization and restoration
- Parallel solver builds
- A separately validated deterministic profile for Windows and Linux
- Editor class documentation

Rapier2D is additive. Installing it does not replace Redot's default physics backend unless a project explicitly selects `Rapier2D`.

Rapier3D is not part of this release. It will remain a separate installable and will only ship if it provides a material user-facing capability beyond Redot Jolt.

## Compatibility

| Component | Supported version |
| --- | --- |
| Engine | Redot 26.2 stable |
| Extension API | Redot's Godot-compatible 4.5.2 API, single precision |
| Platforms | Windows x86-64 and Linux x86-64 |
| Upstream plugin | Godot Rapier Physics 0.35.2 |
| Physics library | Rapier 0.35.1 |
| Rust bindings | [`dominicbytes/redot-rust`](https://github.com/dominicbytes/redot-rust) at `18ad5c538c452b8640420366794354e3ed48f205` |

Each plugin release targets one exact Redot release. macOS, mobile, web, other architectures, and double-precision builds are not supported by the first release line.

## Installation

The current branch contains source and validation records, not an installable release archive. Once the first package is published:

1. Download the Rapier2D archive from [GitHub Releases](https://github.com/dominicbytes/godot-rapier-physics/releases).
2. Extract it into the root of your Redot project. The addon should end up at `addons/godot-rapier2d`.
3. Open the project in Redot 26.2.
4. Enable **Advanced Settings**, then set **Project Settings > Physics > 2D > Physics Engine** to `Rapier2D`.
5. Restart the editor.

To remove the addon, switch the project back to another 2D physics backend before deleting `addons/godot-rapier2d`.

## Project documentation

- [Port and platform matrix](PORT_MATRIX.md)
- [Rapier2D feature-parity ledger](docs/gamedev/rapier2d-parity-ledger.md)
- [Architecture](ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Current release blockers](BLOCKERS.md)

## Credits and licenses

This project is a Redot-focused fork of [appsinacup/godot-rapier-physics](https://github.com/appsinacup/godot-rapier-physics).

The plugin is distributed under the [MIT License](LICENSE). Upstream notices are in [THIRDPARTY.txt](THIRDPARTY.txt); the packaged addon also includes exact dependency notices and MPL-2.0 source-availability information.

## Notes

I vibe coded this in GPT Sol 5.6. I used gauntlet loops and a three step pre-flight, planning, implementation approach to execution. Use at your own risk. Actual programmers are welcome to submit PR's and feedback.

## About Dominic Bytes

Greetings! I am Dominic Bytes, the synth walker. I hail from the distant future. Where brains occupy robot bodies, time travel is a trip to the corner store, and the neon glow of our attire is powered by the light of our souls. Join me on a 1.21 gigawatt powered journey of chill vibes with gaming, anime, movies, and more!

- [Website](https://dominicbytes.carrd.co/)
- [X](https://x.com/DominicBytes)
- [Twitch](https://www.twitch.tv/dominicbytes)
- [YouTube](http://www.youtube.com/@DominicBytes)
- [Kick](https://kick.com/dominicbytes)
