"""Pure resources/download doubles; no runtime or network execution."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pygame_spiel.resources import ModelPaths, asset, default_cache_dir, user_path
ROOT = Path(__file__).resolve().parents[1]


class ResourceTests(unittest.TestCase):
    def test_assets_work_from_other_cwd(self):
        old = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                self.assertTrue(asset("tic_tac_toe/x_image.png").read_bytes().startswith(b"\x89PNG"))
                self.assertTrue(asset("breakthrough/chess_board.png").is_file())
            finally:
                os.chdir(old)
        for invalid in ("../LICENSE", "/absolute.png", "C:/bad", "x\\bad", ""):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                asset(invalid)
        with self.assertRaises(FileNotFoundError):
            asset("missing.png")

    def test_package_assets_work_from_relocated_zip_without_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "relocated.zip"
            with zipfile.ZipFile(bundle, "w") as archive:
                for path in (ROOT / "pygame_spiel").rglob("*"):
                    if path.is_file() and path.suffix in (".py", ".png"):
                        archive.write(path, path.relative_to(ROOT).as_posix())
            code = ("import sys; sys.path.insert(0, sys.argv[1]); "
                    "from pygame_spiel.resources import asset; "
                    "assert asset('tic_tac_toe/x_image.png').read_bytes().startswith(b'\\x89PNG')")
            result = subprocess.run([sys.executable, "-B", "-c", code, str(bundle)],
                                    cwd=tmp, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cache_lookup_is_external_and_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "not-created"
            with patch.dict(os.environ, {"PYGAME_SPIEL_CACHE_DIR": str(cache)}):
                paths = ModelPaths()
                self.assertEqual(default_cache_dir(), cache)
                self.assertEqual(paths.breakthrough_dqn(), cache / "models/dqn/breakthrough/weights_default")
                self.assertFalse(cache.exists())
            for path in (ROOT / "pygame_spiel", ROOT / "pygame_spiel/images/models"):
                with self.assertRaisesRegex(ValueError, "outside"):
                    ModelPaths(path)
                with self.assertRaises(ValueError):
                    user_path(path)
            file = Path(tmp) / "file"
            file.touch()
            with self.assertRaises(ValueError):
                ModelPaths(file)
