# Installation

This source checkout requires Python 3.10+ and a local graphical display.
Runtime dependencies are Pygame 2.5.0, pygame-menu 4.4.3, NumPy `>=1.23.5,<2`,
TensorFlow 2.13.0 and an OpenSpiel 1.3-compatible build. TensorFlow is imported
even for MCTS-only launches and may narrow the supported Python/NumPy versions.
Metadata does not guarantee dependency wheels on every platform or interpreter.

Package-name commands below install the published PyPI release. To use this
checkout's code and model/resource APIs, follow [Clone the repo](#clone-the-repo).

## Just play
If the user just wants to play with the algorithms and games available by default, without changing or adding extra functionalities to Pygame_spiel or OpenSpiel, they can just install the PyPI package and run the game. To install Pygame_spiel run:
```bash
python -m pip install pygame_spiel[spiel]
```
Adding the parameter **[spiel]** within square brackets requests OpenSpiel as a dependency. OpenSpiel is not installed by default, because the main use case in PyGame_spiel is to support users who are working on a local clone of OpenSpiel, and requesting the PyPI distribution may replace a local installation. This checkout's extra pins `open-spiel==1.3`; arbitrary versions and local modifications need integration checks.

NOTE: if you're using a zsh terminal, specify pygame_spiel[spiel] within single quotes:
```bash
python -m pip install 'pygame_spiel[spiel]'
```

To launch Pygame_spiel run:
```bash
pygame_spiel
```

## With the local version of OpenSpiel
If you are working with a OpenSpiel source code locally, you can install PyGame_spiel as an extra library for local development. There are two ways to install PyGame_spiel: 1) clone the repo and install it, 2) via pip install.

### Install via pip
If the user only needs to experiment with new algorithms, and no additional games or changes in the GUI are required, the best way to install Pygame_spiel is via pip install. Unlike with the installation in the previous section, when working with an existing version of OpenSpiel installed locally, run the following:
```bash
python -m pip install 'pygame_spiel'
```
Here we don't specify the parameter **[spiel]**, since we don't want to request an OpenSpiel distribution from pip. Provide importable `pyspiel` and `open_spiel` from a local 1.3-compatible build (see the [OpenSpiel Installation tutorial](https://github.com/google-deepmind/open_spiel/blob/v1.3/docs/install.md)).

### Clone the repo
If you want to customize PyGame_spiel while also working on a local version of OpenSpiel, the simplest way is to clone the repository and install it.
1) Clone pygame_spiel and enter the repository directory.
2) Run `python -m pip install .` with your local OpenSpiel build available.
3) Run `pygame_spiel` from the terminal as usual to launch it.

By cloning the repo the user full access to the code, and the possibility to modify any part of the code (including the graphical UI and elements).

Without a local OpenSpiel build, use `python -m pip install ".[spiel]"` from the
repository root instead. PEP 517 builds use setuptools 84.0.0 and wheel 0.48.0
from [pyproject.toml](../pyproject.toml). The Python minimum covers the build
backend and ZIP resource APIs. Transitive runtime dependencies are not fully
locked. See [Contributing](../CONTRIBUTING.md) for source-check dependencies.

## Models and cache paths

The source application reads checkpoints from external user-owned storage.
Game construction does not download them. From the repository root, install
download support and explicitly request the upstream Breakthrough archive:

```bash
python -m pip install ".[download]"
python -m pygame_spiel.downloads breakthrough
```

The downloader prints the checkpoint directory and refuses an existing destination.
`pygame_spiel_download` is the equivalent installed command. For an alternate cache:

```bash
python -m pygame_spiel.downloads breakthrough --cache-dir /path/to/cache
```

Set `PYGAME_SPIEL_CACHE_DIR` to that same directory before launching the menu.
Without an override, Windows uses `%LOCALAPPDATA%/pygame_spiel` (fallback
`~/AppData/Local/pygame_spiel`), macOS uses `~/Library/Caches/pygame_spiel`, and Linux
uses `$XDG_CACHE_HOME/pygame_spiel` (fallback `~/.cache/pygame_spiel`). Checkpoints
live below `models/dqn/breakthrough/weights_default`. `ModelPaths(cache_dir=...)`
selects the cache in Python. Lookup creates no directories; paths resolving
inside the `pygame_spiel` package are rejected.

For an existing game, `game.set_bots("human", None, "dqn", "/path/to/checkpoint")`
selects an external DQN checkpoint directory for player 1. Pass `None` instead
of a path to use the default cache, as the menu does. An absent checkpoint
fails locally with an explicit preparation command. DQN is Breakthrough-only.

Packaged PNGs are read-only resources accessed through `importlib.resources`:

```python
from pygame_spiel.resources import asset

with asset("tic_tac_toe/x_image.png").open("rb") as stream:
    signature = stream.read(8)
```

## Qualification limits

Real OpenSpiel/Pygame/menu integration, display behavior and checkpoint restoration
are unqualified. Archive availability and integrity are also unqualified.
Source/unit tests use explicit doubles and do not certify a Python/platform/backend
combination or the installed dependency set. A successful package build does not
establish runtime compatibility; see [backend qualification](../CONTRIBUTING.md#backend-qualification).
