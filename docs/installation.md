# Installation

## Just play
If the user just wants to play with the algorithms and games available by default, without changing or adding extra functionalities to Pygame_spiel or OpenSpiel, they can just install the PyPI package and run the game. To install Pygame_spiel run:
```bash
pip install pygame_spiel[spiel]
```
Adding the parameter **[spiel]** within square brackets forces pip to install OpenSpiel as a dependency. OpenSpiel is not installed by default, because the main use case in PyGame_spiel is to support users who are working on a local clone of OpenSpiel, and by specifying it as dependency, the PyPI installation of OpenSpiel would override the local one.

NOTE: if you're using a zsh terminal, specify pygame_spiel[spiel] within single quotes:
```bash
pip install 'pygame_spiel[spiel]'
```

To launch Pygame_spiel run:
```bash
pygame_spiel
```

## With the local version of OpenSpiel
If you are working with a OpenSpiel source code locally, you can install PyGame_spiel as an extra library for local development. There are two ways to install PyGame_spiel: 1) clone the repo and install it, 2) via pip install.

### Install via pip
If the user only needs to experiment with new algorithms, and no additional games or changes in the GUI are required, the best way to install Pygame_spiel is via pip install. Unlike with the installation in the previous section, when working with an existing version of OpenSpiel installed locally, run the following:
```bash
pip install 'pygame_spiel'
```
Here we don't specify the parameter **[spiel]**, since we don't want to override the local version of OpenSpiel with the library from pip. Here we assume that OpenSpiel is already installed locally via pip (as explained in secion 4 in [OpenSpiel Installation tutorial](https://github.com/google-deepmind/open_spiel/blob/master/docs/install.md)).

### Clone the repo
If you want to customize PyGame_spiel while also working on a local version of OpenSpiel, the simplest way is to clone the repository and install it.
1) Clone pygame_spiel
2) run pip install .
3) run pygame_spiel from terminal as usual to launch it

By cloning the repo the user full access to the code, and the possibility to modify any part of the code (including the graphical UI and elements).