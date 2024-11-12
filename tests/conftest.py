"""Config to setup pytest."""

# https://docs.pytest.org/en/stable/fixture.html
# You can use this fixture object in your entire test suite.

# @pytest.fixture
# def example():
#     ...       # setup code
#     yield x   # yield instead of return to use setup/teardown structure
#     ...       # teardown code


import pytest

from choralebricks.dataset import SongDB


@pytest.fixture(name="choralebricks")
def fixture_beatles():
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
