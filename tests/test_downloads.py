"""Pure resources/download doubles; no runtime or network execution."""
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
import zipfile
from pygame_spiel.downloads import download_weights


class DownloadTests(unittest.TestCase):
    def test_download_is_explicit_and_never_overwrites_models(self):
        module = ModuleType("gdown")

        def fake_download(**kwargs):
            with zipfile.ZipFile(kwargs["output"], "w") as archive:
                archive.writestr("weights_default/test-marker.txt", "not model data")
            return kwargs["output"]

        module.download = Mock(side_effect=fake_download)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"gdown": module}):
            destination = Path(tmp) / "external-models"
            self.assertFalse(destination.exists())
            self.assertEqual(download_weights("test-id", destination), destination)
            self.assertTrue((destination / "weights_default/test-marker.txt").is_file())
            with self.assertRaises(FileExistsError):
                download_weights("test-id", destination)
            module.download.assert_called_once()
            self.assertEqual(list(destination.parent.iterdir()), [destination])

    def test_missing_download_extra_leaves_destination_absent(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"gdown": None}):
            destination = Path(tmp) / "not-created" / "models"
            with self.assertRaisesRegex(ImportError, r"pygame_spiel\[download\]"):
                download_weights("test-id", destination)
            self.assertFalse(destination.parent.exists())

    def test_unsafe_archive_and_failed_download_are_retained_as_failures_not_models(self):
        module = ModuleType("gdown")
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"gdown": module}):
            destination = Path(tmp) / "models"

            def unsafe(**kwargs):
                with zipfile.ZipFile(kwargs["output"], "w") as archive:
                    archive.writestr("../escape.txt", "not model data")
                return kwargs["output"]

            module.download = Mock(side_effect=unsafe)
            with self.assertRaisesRegex(ValueError, "unsafe"):
                download_weights("test-id", destination)
            self.assertFalse(destination.exists())
            self.assertFalse((Path(tmp) / "escape.txt").exists())
            module.download = Mock(return_value=None)
            with self.assertRaisesRegex(RuntimeError, "archive"):
                download_weights("test-id", destination)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_package_destination_rejected_before_import_or_network(self):
        import pygame_spiel

        with patch.dict(sys.modules, {"gdown": None}):
            with self.assertRaisesRegex(ValueError, "outside"):
                download_weights("test-id", Path(pygame_spiel.__file__).parent / "data")
