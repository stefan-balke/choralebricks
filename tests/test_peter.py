"""Test ideas from Peter"""

from pathlib import Path

import pandas as pd
import pytest

from choralebricks.dataset import SongDB

TRACKS = [track for song in SongDB().songs for track in song.tracks]
track_ids = [f"{track.path_audio.parts[-3]}-{track.path_audio.stem}" for track in TRACKS]


def test_number_of_songs(songs):
    """Test number of songs"""
    assert len(songs) == 2


@pytest.mark.parametrize("track", TRACKS, ids=track_ids)
def test_paths_not_none(track):
    """Test paths for each track"""
    assert track.path_audio is not None
    assert track.path_f0 is not None
    assert track.path_notes is not None


@pytest.mark.parametrize("track", TRACKS, ids=track_ids)
def test_files_exist(track):
    """Test files exist"""
    assert Path(track.path_audio).exists()
    assert Path(track.path_f0).exists()
    assert Path(track.path_notes).exists()


@pytest.mark.parametrize("track", TRACKS, ids=track_ids)
def test_files_not_empty(track):
    """Test files are not empty"""
    assert Path(track.path_audio).stat().st_size != 0
    assert Path(track.path_f0).stat().st_size != 0
    assert Path(track.path_notes).stat().st_size != 0


@pytest.mark.parametrize("track", TRACKS, ids=track_ids)
def test_track_suffix(track):
    """Test track suffix."""
    assert Path(track.path_audio).suffix == ".wav"
    assert Path(track.path_f0).suffix == ".csv"
    assert Path(track.path_notes).suffix == ".csv"


@pytest.mark.parametrize("track", TRACKS, ids=track_ids)
def test_csv_headers(track):
    """Test CSV file headers"""
    f0_header = pd.read_csv(track.path_f0).columns
    notes_header = pd.read_csv(track.path_notes).columns
    assert list(f0_header) == ['TIME', 'VALUE', 'LABEL']
    assert list(notes_header) == ['TIME', 'VALUE', 'DURATION', 'LEVEL', 'LABEL']
