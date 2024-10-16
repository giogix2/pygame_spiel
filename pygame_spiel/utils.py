import gdown
from pathlib import Path
import importlib.util
import shutil
import os

import pyspiel


def download_weights(file_id, dest_folder):
    """
    Download breakpoints from Google Drive. This function downloads the zip
    file containing the weights, un-compress it in a specified folder and
    delete the temporary zip file.

    Parameters:
        file_id (str): Google Drive file id
        dest_folder (str): folder where the breakpoints are saved

    Returns:
        None
    """

    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    prefix = "https://drive.google.com/uc?/export=download&id="
    url = prefix + file_id
    file_name, suffix = "file", ".zip"
    dest_file_path = Path(dest_folder, file_name).with_suffix(suffix)

    # Download the zip file containing the weights
    gdown.download(url, str(dest_file_path), quiet=False)
    # Uncompress the zip file in dest_folder
    shutil.unpack_archive(dest_file_path, dest_folder)
    # Destroy the temporary zip file
    os.remove(dest_file_path)


def register_classes(file_path: str) -> dict[str, type]:
    """
    Creates new classes definitions from a .py file specified as argument.

    Given the path of a Python file (*.py), this function loads it as a new
    module, and retrieves all the classes contained inside. The classes are
    registered and returned. Only the classes for which the parent is
    pyspiel.Bot are returned. This function is used to allow users to plugin
    new Bots from pygame_spiel menu at runtime.

    Parameters:
        file_path (str): path to a Python file (*.py)

    Returns:
        dict[str, type]: dictionary with class name and class definition
    """
    registered_classes = {}

    module_name = Path(file_path).stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, pyspiel.Bot):
            registered_classes[name] = obj
    return registered_classes
