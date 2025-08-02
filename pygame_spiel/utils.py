from pathlib import Path
import importlib.util

import pyspiel


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
