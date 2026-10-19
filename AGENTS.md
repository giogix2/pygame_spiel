# Working in pygame_spiel

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks and qualification limits.
Use `python -B -W error -m unittest discover -s tests -v` from the repository root.

## Owners and boundaries

Package paths below are relative to `pygame_spiel/`.

- `games/base.py` owns OpenSpiel state and controller construction; concrete games
  own rendering/mouse mapping. `games/settings.py` owns game/menu constants.
- `main.py` owns the display/event loop; `menu.py` owns selection; `utils.py`
  owns the developer Python bot-file loader. These import runtime dependencies.
- `resources.py` owns read-only image lookup and external model/cache paths.
  Lookup must not write. `downloads.py` alone fetches/extracts models explicitly.
- `bots/dqn.py` imports TensorFlow eagerly through the game base. Do not mark it
  optional until every ordinary import consumer supports that boundary.

OpenSpiel owns game rules and legal actions. Do not duplicate them in a renderer.
Do not introduce downloads or mutable package-directory writes during imports,
resource lookup or construction. Display creation currently occurs in constructors;
keep unit checks on explicit doubles and qualify real backends separately.

When replacing an implementation, migrate all consumers, delete the replaced
implementation, and remove tests/fixtures/assets whose sole consumer disappeared.
Keep compatibility only for a named currently supported consumer; obsolete tests
alone do not justify retaining code. Document public contract changes.

## Maintained documentation

- Describe the current supported system and verify instructions against code.
- Keep completed-work reports and run evidence outside maintained product docs.
- Remove superseded prose when its replacement lands.
- Active plans contain remaining work, dependencies and acceptance criteria;
  update or retire them when completed.
- Review the surviving reading path, including untouched documents and links,
  rather than only the diff.
- Historical explanation needs a concrete present-day compatibility or decision purpose.
