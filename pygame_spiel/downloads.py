"""Explicit opt-in download of the upstream Breakthrough TensorFlow checkpoint."""

import argparse
from pathlib import Path
import tempfile
import zipfile

from pygame_spiel.resources import ModelPaths, user_path


BREAKTHROUGH_DQN_DRIVE_ID = "1c7y-vFezKvNF6qT3kGgEodkv0z6kvwPZ"


def download_weights(file_id: str, dest_folder) -> Path:
    """Download/extract into a new external directory. Never overwrite models."""
    destination = user_path(dest_folder)
    if not file_id or not isinstance(file_id, str):
        raise ValueError("A Google Drive file ID is required")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing models: {destination}")
    try:
        import gdown
    except ImportError as exc:
        raise ImportError("Downloads require the 'pygame_spiel[download]' extra") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pygame-spiel-", dir=destination.parent) as tmp:
        archive = Path(tmp) / "weights.zip"
        result = gdown.download(id=file_id, output=str(archive), quiet=False)
        if result is None or not archive.is_file():
            raise RuntimeError("Weight download did not produce an archive")
        extracted = Path(tmp) / "models"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (extracted / member.filename).resolve()
                if extracted not in target.parents or "\\" in member.filename:
                    raise ValueError("Weight archive contains an unsafe path")
            bundle.extractall(extracted)
        if destination.exists():
            raise FileExistsError(f"Model destination appeared during download: {destination}")
        extracted.rename(destination)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=["breakthrough"])
    parser.add_argument("--cache-dir", type=Path)
    args = parser.parse_args(argv)
    paths = ModelPaths(args.cache_dir) if args.cache_dir else ModelPaths()
    destination = paths.breakthrough_dqn().parent
    download_weights(BREAKTHROUGH_DQN_DRIVE_ID, destination)
    print(paths.breakthrough_dqn())


if __name__ == "__main__":
    main()
