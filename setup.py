from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

def read_requirements():
    with open("requirements.txt", "r") as f:
        return [x for x in f.read().splitlines() if x != ""]

setup(
    name="pygame_spiel",
    version="0.1.1",
    author="Giovanni Ortolani",
    author_email="giovorto@pm.me",
    description="Pygame spiel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/giogix2/pygame_spiel",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={'': ['pygame_spiel/images/*']},
    python_requires=">=3.9.1",
    entry_points={
        'console_scripts': [
            'pygame_spiel = pygame_spiel.main:pygame_spiel'
        ]
    }
)