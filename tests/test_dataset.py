"""
All tests related to dataset.py and the involved logic.
"""
from pathlib import Path

import pytest

from choralebricks.constants import Instrument
from choralebricks.dataset import EnsemblePermutations, Song, Track


@pytest.fixture
def mockupdb():
    """Mockup database with a single song."""
  
    def mocktrack(
        voice: int,
        instrument: Instrument
    ):
        
        track = Track(
            song_id="test_song_01",
            path_audio=f"{instrument.value}_{voice}.wav",
            num_channels=1,
            sample_rate=44100,
            min_samples=441000,
            voice=voice,
            instrument=instrument
        )
        
        return track
 
    song01_tracks = [
        mocktrack(1, Instrument.TRUMPET),
        mocktrack(1, Instrument.CLARINET),
        mocktrack(2, Instrument.TRUMPET),
        mocktrack(2, Instrument.CLARINET),
        mocktrack(3, Instrument.BARITONE),
        mocktrack(4, Instrument.BARITONE),
        mocktrack(4, Instrument.TUBA),
    ]

    song_01 = Song(Path("song_01"))
    song_01.tracks = song01_tracks

    return [song_01, ]


@pytest.fixture
def ensembles(mockupdb):
    """All Possible Ensemble Permutations"""
    return [ens for song in mockupdb for ens in EnsemblePermutations(song)]


def test_number_of_songs(mockupdb):
    """Test number of songs"""
    assert len(mockupdb) == 1


def test_number_of_ensembles(ensembles):
    """Test number of ensembles"""
    assert len(ensembles) == 2 * 2 * 1 * 2


def test_instrument_type(mockupdb):
    """Test number of songs"""
    
    for cur_song in mockupdb:
        for cur_track in cur_song.tracks:
            assert cur_track.instrument_type != None


def test_import_my_module():
    # Attempt to import the module
    try:
        import choralebricks.dataset
    except ImportError:
        pytest.fail("Importing my_module failed")
