from .dataset import SongDB


def tracks():
    """
    Generator that yields all the available tracks in the dataset.
    
    Use it, when you just need the pathes to the audio files
    and you are not interested in the song relations,
    e.g., when doing F0-extraction on monophonic audio singals.
    """
    cbdb = SongDB(root_dir="/Users/stefan/dev/wind_music_db/data/02_multitrack")

    for cur_song in cbdb.songs:
        for cur_track in cur_song.tracks:
            yield cur_track

def brass_ensemble_songs():
    """
    Generator that yields all songs as a pre-defined brass ensemble:
    1. Trumpet
    2. Trumpet
    3. Baritone
    4. Tuba
    """
    # TODO: build logic
    pass

def ww_ensemble_songs():
    """
    Generator that yields all songs as a pre-defined woodwinds ensemble:
    1. Clarinet
    2. Clarinet
    3. Bass Clarinet
    4. Bass Clarinet
    """
    # TODO: build logic
    pass
