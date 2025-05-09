import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from choralebricks.dataset import EnsemblePermutations, SongDB
from choralebricks.utils import read_f0_sv, read_f0, read_notes, read_chords
from choralebricks import ChordSequence


# Check for the environment variable CHORALEDB_PATH
choraledb_path = os.getenv('CHORALEDB_PATH')

if choraledb_path:
    TRACKS = [track for song in SongDB().songs for track in song.tracks]
    tr_ids = [f"{track.song_id}-{track.path_audio.stem}" for track in TRACKS]
else:
    TRACKS = []
    tr_ids = []

"""
    Test Fixtures
"""
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


"""
    Data Integration Tests
"""
def test_number_of_songs(songs):
    """Test number of songs"""
    assert len(songs) == 10


def test_number_of_ensembles(ensembles):
    """Test number of ensembles"""
    assert len(ensembles) == 4582


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_paths_audio_not_none(track):
    """Test paths for each track"""
    assert track.path_audio is not None


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_paths_f0_not_none(track):
    """Test paths for each track"""
    assert track.path_f0 is not None


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_paths_notes_not_none(track):
    """Test paths for each track"""
    assert track.path_notes is not None


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_files_exist(track):
    """Test files exist"""
    assert Path(track.path_audio).exists()
    assert Path(track.path_f0).exists()
    assert Path(track.path_notes).exists()


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_files_not_empty(track):
    """Test files are not empty"""
    assert Path(track.path_audio).stat().st_size != 0
    assert Path(track.path_f0).stat().st_size != 0
    assert Path(track.path_notes).stat().st_size != 0


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_track_suffix(track):
    """Test track suffix."""
    assert Path(track.path_audio).suffix == ".wav"
    assert Path(track.path_f0).suffix == ".csv"
    assert Path(track.path_notes).suffix == ".csv"


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_csv_headers(track):
    """Test CSV file headers from Sonic Visualizer."""
    path_sv_f0 = Path(str(track.path_f0).replace("_filled", ""))
    f0_head = read_f0_sv(path_sv_f0, rename_cols=False).columns if track.path_f0 else []
    notes_head = read_notes(track.path_notes, rename_cols=False).columns if track.path_notes else []
    assert list(f0_head) == ["TIME", "VALUE", "LABEL"]
    assert list(notes_head) == ["TIME", "VALUE", "DURATION", "LEVEL", "LABEL"]


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_track_samplerate(track):
    """Test if all tracks have the same samplerate."""
    if track.path_audio:
        _, sr = sf.read(track.path_audio)
        assert sr == track.sample_rate


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_track_min_samples(track):
    """Test if track has the given min_samples."""
    if track.path_audio:
        data, _ = sf.read(track.path_audio)
        assert len(data) == track.min_samples


def test_track_len_per_song(songs):
    """Test if all songs have tracks with same number of samples."""
    for song in songs:
        track_lengths = []
        for track in song.tracks:
            if track.path_audio:
                data, _ = sf.read(track.path_audio)
                track_lengths.append(len(data))
        assert len(set(track_lengths)) <= 1, f"Not all audio files of {song.id} have the same length."


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_dur_f0_audio(track):
    """Audio and F0-annotations should have similar length (+-1 seconds)"""
    dur_audio = track.min_samples / track.sample_rate
    path_sv_f0 = Path(str(track.path_f0).replace("_filled", ""))
    dur_f0 = read_f0_sv(path_sv_f0).tail(1)["t"].values[0]
    assert np.abs(dur_audio - dur_f0) < 1.0


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_f0_trajectory_uniqueness(track):
    """All F0-trajectories should have only one entry per time instance"""
    df = read_f0(track.path_f0)
    assert df.shape[0] == df.drop_duplicates("t").shape[0]


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_dur_note_audio(track):
    """Audio and note annotations should have similar length (+-1 seconds)"""
    dur_audio = track.min_samples / track.sample_rate
    last_note = read_notes(track.path_notes).tail(1)
    dur_notes = (last_note["t_start"] + last_note["t_dur"]).values[0]
    assert np.abs(dur_audio - dur_notes) < 1.0


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_chord_csv(track):
    """Test chord CSV."""
    csv_header = read_chords(track.path_chords).columns if track.path_chords else []
    assert list(csv_header) == ["start_meas", "end_meas", "chord"]


@pytest.mark.parametrize("track", TRACKS, ids=tr_ids)
def test_chord_annotations_sequence(track):
    """Test if CSV chord annotations can be parsed into a ChordSequence"""

    # all tracks link to the same chord annotations, so we only take one
    cs = ChordSequence.from_csv(track.path_chords)
    # all songs should have a chord in the second measure
    assert cs.get_chord_at(2.25).root is not None, f"Chord for song {track.song_id} not parsed correctly."
    for i in range(len(cs.bounds)-1):
        if cs.bounds[i,1] > cs.bounds[i+1,0]:
            print(track.song_id, i, cs.bounds[i,1], cs.bounds[i+1,0])
    assert np.all(cs.bounds[:-1,1] <= cs.bounds[1:,0]), f"Overlapping chord annotations for song {track.song_id}."
