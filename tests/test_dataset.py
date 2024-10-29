import pytest
from choralebricks.dataset import SongDB, TrackSelectorRandom, MixerSimple


def test_import_my_module():
    # Attempt to import the module
    try:
        import choralebricks.dataset
    except ImportError:
        pytest.fail("Importing my_module failed")

def test_track_selector_random():
    cbdb = SongDB(root_dir="/Users/stefan/dev/wind_music_db/data/02_multitrack")

    for cur_song in cbdb.songs:
        cur_song_filtered = TrackSelectorRandom(cur_song).song
        assert len(cur_song_filtered.tracks) == 4
