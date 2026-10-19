"""Immutable package assets and user-owned model locations (no writes on lookup)."""

from dataclasses import dataclass, field
from importlib.resources import files
import os
from pathlib import Path, PurePosixPath
import sys


def asset(name: str):
    """Return a Traversable on Python 3.10+, including imports from a zip."""
    path = PurePosixPath(name)
    if (not path.parts or path.is_absolute() or ".." in path.parts
            or "\\" in name or ":" in name):
        raise ValueError("Asset name must be a relative package resource path")
    resource = files("pygame_spiel").joinpath("images", *path.parts)
    if not resource.is_file():
        raise FileNotFoundError(f"Packaged asset not found: {name}")
    return resource


def user_path(path) -> Path:
    """Resolve an external path, rejecting the installed/source package tree."""
    resolved = Path(path).expanduser().resolve()
    package = Path(__file__).resolve().parent
    if resolved == package or package in resolved.parents:
        raise ValueError("Models and cache must be outside the pygame_spiel package")
    return resolved


def default_cache_dir() -> Path:
    override = os.environ.get("PYGAME_SPIEL_CACHE_DIR")
    if override:
        return user_path(override)
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return user_path(root / "pygame_spiel")


@dataclass(frozen=True)
class ModelPaths:
    cache_dir: Path = field(default_factory=default_cache_dir)

    def __post_init__(self):
        path = user_path(self.cache_dir)
        if path.exists() and not path.is_dir():
            raise ValueError(f"cache_dir must be a directory: {path}")
        object.__setattr__(self, "cache_dir", path)

    def breakthrough_dqn(self) -> Path:
        return user_path(self.cache_dir / "models" / "dqn" / "breakthrough" / "weights_default")
