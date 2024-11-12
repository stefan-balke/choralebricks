"""Test ideas from Peter"""

from pathlib import Path

import pytest

from choralebricks.dataset import SongDB


def test_number_of_songs(songs):
    """Test number of songs"""
    assert len(songs) == 2


tracks = [track for song in SongDB().songs for track in song.tracks]


@pytest.mark.parametrize("track", tracks)
def test_paths_not_none(track):
    """Test paths for each track"""
    assert track.path_audio is not None
    assert track.path_f0 is not None
    assert track.path_notes is not None


@pytest.mark.parametrize("track", tracks)
def test_files_exist(track):
    """Test files exist"""
    assert Path(track.path_audio).exists()
    assert Path(track.path_f0).exists()
    assert Path(track.path_notes).exists()


@pytest.mark.parametrize("track", tracks)
def test_files_not_empty(track):
    """Test files are not empty"""
    assert Path(track.path_audio).stat().st_size != 0
    assert Path(track.path_f0).stat().st_size != 0
    assert Path(track.path_notes).stat().st_size != 0
