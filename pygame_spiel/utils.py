import numpy as np
import gdown
import pathlib
import shutil
import os

import pyspiel
from pygame_spiel.bots import dqn

from open_spiel.python.bots import uniform_random, human
from open_spiel.python.algorithms import mcts


def init_bot(
    bot_type: str, game: pyspiel.Game, player_id: int, breakpoint_dir: str = None
) -> None:
    """
    Returns a bot of type bot_type for the player specified by player_id.

    Parameters:
        bot_type (str): Bot type (mcts, random or dqn)
        game (pyspiel.Game): open_spiel game
        player_id (int): id of the player that the bot will be driving
        breakpoint_dir (str): Path to the DQN weigths (optional)

    Returns:
        None
    """
    rng = np.random.RandomState(42)
    if bot_type == "mcts":
        utc = 2  # UCT's exploration constant
        max_simulations = 1000
        rollout_count = 1
        evaluator = mcts.RandomRolloutEvaluator(rollout_count, rng)
        solve = True  # Whether to use MCTS-Solver.
        verbose = False
        bot = mcts.MCTSBot(
            game,
            utc,
            max_simulations,
            evaluator,
            random_state=rng,
            solve=solve,
            verbose=verbose,
        )
        return bot
    if bot_type == "random":
        bot = uniform_random.UniformRandomBot(1, rng)
        return bot
    if bot_type == "dqn":
        # We need to load bots for both players, because the models have been trained
        # using the script breakthrough_dqn.py, causing the issue reported in
        # https://github.com/deepmind/open_spiel/issues/1104.
        # Only the both related to the specified player is returned.
        bot0 = dqn.DQNBot(game, player_id=0, checkpoint_dir=breakpoint_dir)
        bot1 = dqn.DQNBot(game, player_id=1, checkpoint_dir=breakpoint_dir)
        return bot0 if player_id == 0 else bot1
    if bot_type == "human":
        return human.HumanBot()
    raise ValueError("Invalid bot type: %s" % bot_type)


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

    pathlib.Path(dest_folder).mkdir(parents=True, exist_ok=True)
    prefix = "https://drive.google.com/uc?/export=download&id="
    url = prefix + file_id
    file_name, suffix = "file", ".zip"
    dest_file_path = pathlib.Path(dest_folder, file_name).with_suffix(suffix)

    # Download the zip file containing the weights
    gdown.download(url, str(dest_file_path), quiet=False)
    # Uncompress the zip file in dest_folder
    shutil.unpack_archive(dest_file_path, dest_folder)
    # Destroy the temporary zip file
    os.remove(dest_file_path)
