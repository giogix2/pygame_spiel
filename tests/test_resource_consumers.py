"""Resource/model consumer contracts with explicit graphics/game/neural doubles."""

import importlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

# Load NumPy before sys.modules snapshots, so it is not reimported on teardown.
import numpy

ROOT = Path(__file__).resolve().parents[1]


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        names = ['pygame', 'pyspiel', 'open_spiel', 'open_spiel.python',
                 'open_spiel.python.bots', 'open_spiel.python.bots.uniform_random',
                 'open_spiel.python.bots.human', 'open_spiel.python.algorithms',
                 'open_spiel.python.algorithms.mcts', 'pygame_spiel.bots.dqn']
        modules = {name: ModuleType(name) for name in names}
        for name, module in modules.items():
            module.__path__ = []
            if '.' in name and name.rsplit('.', 1)[0] in modules:
                parent, child = name.rsplit('.', 1)
                setattr(modules[parent], child, module)
        modules['pyspiel'].Game = object
        modules['pyspiel'].load_game = Mock()
        pg = modules['pygame']
        for name in ('init', 'display', 'image', 'font', 'transform'):
            setattr(pg, name, Mock())
        runtime = patch.dict(sys.modules, modules)
        runtime.start()
        self.addCleanup(runtime.stop)
        # Ensure each import really exercises these doubles and this checkout.
        for name in list(sys.modules):
            if name.startswith('pygame_spiel.games'):
                sys.modules.pop(name)
        self.pg = pg
        self.base = importlib.import_module('pygame_spiel.games.base')

    def test_renderers_read_all_assets_as_streams(self):
        from pygame_spiel.games.tic_tac_toe import TicTacToe
        from pygame_spiel.games.breakthrough import Breakthrough

        loaded = []
        def load(stream, name):
            self.assertTrue(stream.read(8).startswith(b'\x89PNG'))
            loaded.append(name)
            return Mock()
        self.pg.image.load.side_effect = load
        for cls, name in ((TicTacToe, 'tic_tac_toe'), (Breakthrough, 'breakthrough')):
            cls(name, 0)
        self.assertEqual(set(loaded), {p.relative_to(ROOT / 'pygame_spiel/images').as_posix()
                                      for p in (ROOT / 'pygame_spiel/images').rglob('*.png')})
        self.assertEqual(len(loaded), 5)

    def test_model_consumer_uses_external_cache_or_explicit_path_without_fetch(self):
        game = object.__new__(type('Concrete', (self.base.Game,), {'play': lambda *args: None}))
        game._name, game._game = 'breakthrough', object()
        game._init_bot = Mock(return_value=object())
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {'PYGAME_SPIEL_CACHE_DIR': tmp}):
            with self.assertRaisesRegex(FileNotFoundError, 'downloads breakthrough'):
                game.set_bots('human', None, 'dqn', None)
            expected = Path(tmp) / 'models/dqn/breakthrough/weights_default'
            expected.mkdir(parents=True)
            game.set_bots('human', None, 'dqn', None)
            self.assertEqual(game._init_bot.call_args.kwargs['breakpoint_dir'], expected)
            custom = Path(tmp) / 'custom'
            custom.mkdir()
            game.set_bots('human', None, 'dqn', custom)
            self.assertEqual(game._init_bot.call_args.kwargs['breakpoint_dir'], custom)
            with self.assertRaisesRegex(ValueError, 'outside'):
                game.set_bots('human', None, 'dqn', ROOT / 'pygame_spiel/data')

    def test_pure_modules_and_download_help_do_not_import_backends(self):
        code = '''
import importlib.abc, runpy, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in ('pygame','pyspiel','open_spiel','tensorflow','gdown','numpy'):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
import pygame_spiel.resources, pygame_spiel.downloads
sys.argv = ['pygame_spiel.downloads', '--help']
from pygame_spiel.downloads import main
main()
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--cache-dir', result.stdout)

    def test_missing_open_spiel_has_installation_choices(self):
        code = '''
import sys, types
sys.modules['pygame'] = types.ModuleType('pygame')
sys.modules['pyspiel'] = None
try:
    import pygame_spiel.games.base
except ImportError as exc:
    assert 'pygame_spiel[spiel]' in str(exc), str(exc)
    assert 'local OpenSpiel 1.3' in str(exc), str(exc)
else:
    raise AssertionError('Missing dependency was accepted')
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
