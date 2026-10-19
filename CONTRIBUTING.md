# Contributing

Use a separate Python 3.10 or 3.11 environment for source checks. These versions
have wheels for the pinned NumPy 1.24.3 test dependency and are within the intended
TensorFlow 2.13 generation. Install only the test requirements for unit/package work:

```bash
python -m pip install -r requirements-test.txt
python -B -W error -m unittest discover -s tests -v
```

Run from the repository root. Discovery executes each `test_*.py` once; do not
import TestCase classes into another test module. Tests check that imports target
this checkout. The suite builds wheel/sdist artifacts in temporary copies without
installing the application, resolving runtime dependencies or contacting a server.
Staging selects required build files and the current package, image, documentation
and test directories before copying; local environments, caches and unrelated root
artifacts are not traversed or copied. The same staging check runs on the unpacked
source archive without Git. New source/data directories need an explicit selection
in `tests/test_packaging.py`.
It checks packaged source/assets/license, metadata, ZIP resource lookup, a source
archive roundtrip, documentation links/example syntax and explicit consumer doubles.
Build tests need the declared setuptools/wheel versions. A missing tool is a setup
failure, not a skipped successful package check.

[CI](.github/workflows/checks.yml) runs this command on Linux Python 3.10/3.11
with the declared test requirements. Those jobs are source/unit/package checks;
they do not install the graphical/neural application dependencies.

For application development, follow [installation](docs/installation.md), including
the choice between a local OpenSpiel build and `[spiel]`. See
[bot-file extension](docs/get_started.md#register-a-new-bot) and
[agent guidance](AGENTS.md) for owners.
Keep tests and necessary user/API documentation with the code they verify.

## Backend qualification

Unit doubles establish argument, resource and import contracts only. They cannot
qualify real OpenSpiel constructors/actions, Pygame rendering/input, menu callbacks
or TensorFlow checkpoint restoration. A suitable separately provisioned environment
must check real random/MCTS construction, legal action/state transitions and installed
image loading, then display behavior and DQN restoration separately. Record exact
Python/backend versions, platform, checkpoint identity and results outside product
docs. No backend combination is currently certified; see the
[current limits](docs/installation.md#qualification-limits).
