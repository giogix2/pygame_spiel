"""No-install archive checks; no game, graphics, network or model execution."""

from email.parser import BytesParser
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def stage_source(source, destination):
    """Copy the current flat source layout, without scanning unrelated subtrees.

    Keep new build inputs explicit here. No Git metadata or generated egg-info
    is needed, so the same selection works on an unpacked source distribution.
    """
    required = (
        "pyproject.toml", "MANIFEST.in", "LICENSE", "main.py",
        "README.md", "AGENTS.md", "CONTRIBUTING.md", "requirements-test.txt",
        ".github/workflows/checks.yml", "pygame_spiel/__init__.py",
        "pygame_spiel/bots/__init__.py", "pygame_spiel/games/__init__.py",
        "docs/installation.md", "docs/get_started.md",
        "docs/images/module_dropdown_1.png", "docs/images/module_dropdown_2.png",
        "docs/images/module_dropdown_3.png",
        "tests/test_packaging.py", "pygame_spiel/images/tic_tac_toe/x_image.png",
        "pygame_spiel/images/breakthrough/chess_board.png",
        "pygame_spiel/images/breakthrough/pawn_black.png",
        "pygame_spiel/images/breakthrough/pawn_white.png",
        "pygame_spiel/images/breakthrough/pawn_white_selected.png",
    )
    missing = [name for name in required if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError("Required package-check inputs missing: " + ", ".join(missing))
    selected = {Path(name) for name in required}
    for pattern in ("pygame_spiel/*.py", "pygame_spiel/bots/*.py",
                    "pygame_spiel/games/*.py", "pygame_spiel/images/breakthrough/*.png",
                    "pygame_spiel/images/tic_tac_toe/*.png", "docs/*.md", "tests/*.py"):
        selected.update(path.relative_to(source) for path in source.glob(pattern) if path.is_file())
    # Select before copying: never copy an environment and remove it afterwards.
    for relative in sorted(selected):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    return tuple(sorted(selected))


class StagingTests(unittest.TestCase):
    def make_source(self, root):
        # Independent tiny fixture, with bytes that must survive unchanged.
        names = (
            "pyproject.toml", "MANIFEST.in", "LICENSE", "main.py", "README.md",
            "AGENTS.md", "CONTRIBUTING.md", "requirements-test.txt",
            ".github/workflows/checks.yml", "pygame_spiel/__init__.py",
            "pygame_spiel/bots/__init__.py", "pygame_spiel/bots/example.py",
            "pygame_spiel/games/__init__.py", "pygame_spiel/games/example.py",
            "pygame_spiel/main.py", "docs/installation.md", "docs/get_started.md",
            "docs/next_milestone.md", "tests/test_packaging.py",
            "docs/images/module_dropdown_1.png", "docs/images/module_dropdown_2.png",
            "docs/images/module_dropdown_3.png",
            "tests/support.py", "pygame_spiel/images/tic_tac_toe/x_image.png",
            "pygame_spiel/images/breakthrough/chess_board.png",
            "pygame_spiel/images/breakthrough/pawn_black.png",
            "pygame_spiel/images/breakthrough/pawn_white.png",
            "pygame_spiel/images/breakthrough/pawn_white_selected.png",
        )
        expected = {}
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            expected[name] = (name + "\r\n").encode() + b"\x00\xff"
            path.write_bytes(expected[name])
        return expected

    def test_selected_inputs_preserve_bytes_without_visiting_local_artifacts(self):
        for git_checkout in (False, True):
            with self.subTest(git_checkout=git_checkout), tempfile.TemporaryDirectory() as tmp:
                source, destination = Path(tmp) / "source", Path(tmp) / "staged"
                expected = self.make_source(source)
                if git_checkout:
                    (source / ".git").write_text("gitdir: unused")
                excluded = [source / name for name in (
                    ".venv", "local-evidence", ".cache", "pygame_spiel/__pycache__",
                    "pygame_spiel/.venv", "docs/.cache", "docs/images/.cache", "tests/local-artifacts",
                    "pygame_spiel/images/local-artifacts")]
                for directory in excluded:
                    (directory / "site-packages").mkdir(parents=True)
                    (directory / "site-packages/marker.py").write_bytes(b"excluded")
                (source / "unrelated-report.md").write_text("not maintained documentation")
                (source / "PKG-INFO").write_text("generated source archive metadata")
                scandir = os.scandir
                copy2 = shutil.copy2
                def checked_scandir(path):
                    path = Path(path).resolve()
                    if any(path == directory or directory in path.parents for directory in excluded):
                        raise AssertionError(f"Traversed excluded directory: {path}")
                    return scandir(path)
                def checked_copy(path, target):
                    self.assertIn(Path(path).relative_to(source).as_posix(), expected)
                    return copy2(path, target)
                with patch("os.scandir", side_effect=checked_scandir), \
                        patch("shutil.copy2", side_effect=checked_copy), \
                        patch("subprocess.run", side_effect=AssertionError("Staging must not run Git/tools")):
                    selected = stage_source(source, destination)
                self.assertEqual({path.as_posix() for path in selected}, set(expected))
                actual = {path.relative_to(destination).as_posix(): path.read_bytes()
                          for path in destination.rglob("*") if path.is_file()}
                self.assertEqual(actual, expected)
                self.assertEqual((source / ".git").exists(), git_checkout)

    def test_missing_required_inputs_fail_before_copying(self):
        for missing in ("pyproject.toml", "MANIFEST.in", "LICENSE", "README.md",
                        "docs/get_started.md", "docs/images/module_dropdown_2.png",
                        "pygame_spiel/games/__init__.py",
                        "pygame_spiel/images/breakthrough/pawn_black.png",
                        "requirements-test.txt", ".github/workflows/checks.yml",
                        "tests/test_packaging.py", "main.py"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                source, destination = Path(tmp) / "source", Path(tmp) / "staged"
                self.make_source(source)
                (source / missing).unlink()
                with self.assertRaisesRegex(FileNotFoundError, "Required package-check inputs missing") as error:
                    stage_source(source, destination)
                self.assertIn(missing, str(error.exception))
                self.assertFalse(destination.exists())


class PackagingTests(unittest.TestCase):
    def test_wheel_sdist_and_relocated_resources(self):
        # Copy source: build_meta may write build/ and egg-info beside its input.
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "source"
            inputs = stage_source(ROOT, staging)
            output = Path(tmp) / "artifacts"
            output.mkdir()
            script = """
import setuptools.build_meta as backend, sys
destination = sys.argv[1]  # build_meta replaces sys.argv while invoking setup.
backend.build_sdist(destination)
backend.build_wheel(destination)
"""
            env = dict(os.environ, SOURCE_DATE_EPOCH="1786872999", PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-B", "-c", script, str(output)],
                                    cwd=staging, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            wheel, = output.glob("*.whl")
            sdist, = output.glob("*.tar.gz")
            with zipfile.ZipFile(wheel) as archive:
                names = archive.namelist()
                metadata = BytesParser().parsebytes(archive.read(next(
                    n for n in names if n.endswith(".dist-info/METADATA"))))
                self.assertEqual(metadata["Requires-Python"], ">=3.10")
                requirements = metadata.get_all("Requires-Dist")
                self.assertIn('tensorflow==2.13.0', requirements)
                self.assertIn('open-spiel==1.3; extra == "spiel"', requirements)
                self.assertFalse(any(r.startswith("open-spiel") and ";" not in r for r in requirements))
                self.assertIn('gdown==5.2.2; extra == "download"', requirements)
                entries = archive.read(next(n for n in names if n.endswith("/entry_points.txt"))).decode()
                self.assertIn("pygame_spiel = pygame_spiel.main:pygame_spiel", entries)
                self.assertIn("pygame_spiel_download = pygame_spiel.downloads:main", entries)
                self.assertEqual(archive.read(next(n for n in names if n.endswith("/licenses/LICENSE"))),
                                 (ROOT / "LICENSE").read_bytes())
                expected = {p.as_posix() for p in inputs if p.parts[0] == "pygame_spiel"}
                actual = {n for n in names if n.startswith("pygame_spiel/")}
                self.assertEqual(actual, expected)
                for name in expected:
                    source, packaged = (ROOT / name).read_bytes(), archive.read(name)
                    if name.endswith(".py"):
                        source, packaged = source.replace(b"\r\n", b"\n"), packaged.replace(b"\r\n", b"\n")
                    self.assertEqual(packaged, source, name)
            with tarfile.open(sdist) as archive:
                members = archive.getmembers()
                prefix = members[0].name.split("/")[0]
                distributed = {m.name.removeprefix(prefix + "/") for m in members if m.isfile()}
                for relative in inputs:
                    name = relative.as_posix()
                    path = ROOT / relative
                    self.assertIn(name, distributed)
                    self.assertEqual(archive.extractfile(prefix + "/" + name).read(), path.read_bytes(), name)
                self.assertEqual(BytesParser().parsebytes(archive.extractfile(prefix + "/PKG-INFO").read())
                                 ["Requires-Python"], ">=3.10")
                # Archives are produced from this staging tree; reject traversal before extraction.
                extracted = Path(tmp) / "roundtrip"
                for member in members:
                    target = (extracted / member.name).resolve()
                    self.assertIn(extracted.resolve(), target.parents)
                    self.assertFalse(member.issym() or member.islnk())
                archive.extractall(extracted, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
            rebuilt = Path(tmp) / "rebuilt"
            rebuilt.mkdir()
            source_archive = extracted / prefix
            self.assertFalse((source_archive / ".git").exists())
            restaged = Path(tmp) / "from-sdist"
            self.assertEqual(stage_source(source_archive, restaged), inputs)
            result = subprocess.run([sys.executable, "-B", "-c",
                                     "import setuptools.build_meta as b, sys; b.build_wheel(sys.argv[1])",
                                     str(rebuilt)], cwd=restaged, env=env,
                                    capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(wheel.read_bytes(), (rebuilt / wheel.name).read_bytes())
            code = r"""
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in ('pygame','pygame_menu','pyspiel','open_spiel','tensorflow','torch','gdown','numpy'):
            raise AssertionError('Unexpected backend: ' + fullname)
sys.meta_path.insert(0, Block())
sys.path.insert(0, sys.argv[1])
import pygame_spiel
assert sys.argv[1] in pygame_spiel.__file__, pygame_spiel.__file__
from pygame_spiel.resources import asset, ModelPaths
for name in sys.argv[2:]:
    assert asset(name).read_bytes().startswith(b'\x89PNG')
ModelPaths()
"""
            images = sorted(p.relative_to("pygame_spiel/images").as_posix()
                            for p in inputs if p.parts[:2] == ("pygame_spiel", "images")
                            and p.suffix == ".png")
            result = subprocess.run([sys.executable, "-B", "-c", code, str(wheel), *images],
                                    cwd=tmp, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
