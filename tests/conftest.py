"""Config to setup pytest."""

# https://docs.pytest.org/en/stable/fixture.html
# You can use this fixture object in your entire test suite.

# @pytest.fixture
# def example():
#     ...       # setup code
#     yield x   # yield instead of return to use setup/teardown structure
#     ...       # teardown code


import pytest

from choralebricks.dataset import EnsemblePermutations, SongDB


@pytest.fixture(name="choralebricks")
def songdb():
    """ChoraleBricks Dataset"""
    choralebricks = SongDB()
    yield choralebricks


@pytest.fixture
def tracks(choralebricks):
    """All Dataset Tracks"""
    return [track for song in choralebricks.songs for track in song.tracks]


@pytest.fixture
def songs(choralebricks):
    """All Dataset Songs"""
    return choralebricks.songs


@pytest.fixture
def ensembles(choralebricks):
    """All Possible Ensemble Permutations"""
    return [ens for song in choralebricks.songs for ens in EnsemblePermutations(song)]
