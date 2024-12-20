from choralebricks.dataset import SongDB


def tracks():
    """
    Generator that yields all the available tracks in the dataset.
    
    Use it, when you just need the pathes to the audio files
    and you are not interested in the song relations,
    e.g., when doing F0-extraction on monophonic audio singals.
    """
    cbdb = SongDB()

    for cur_song in cbdb.songs:
        for cur_track in cur_song.tracks:
            yield cur_track

def brass_ensemble_songs():
    """
    Generator that yields all songs as a pre-defined brass ensemble:
    1. Voice: Trumpet
    2. Voice: Trumpet
    3. Voice: Baritone
    4. Voice: Tuba
    """
    # TODO: build logic
    pass

def ww_ensemble_songs():
    """
    Generator that yields all songs as a pre-defined woodwinds ensemble:
    1. Voice: Clarinet
    2. Voice: Clarinet
    3. Voice: Bass Clarinet
    4. Voice: Bass Clarinet
    """
    # TODO: build logic
    pass

def mixed_ensemble_songs():
    """
    Generator that yields all songs as a pre-defined ensemble with mixed instruments:
    1. Voice: tbd
    2. Voice: tbd
    3. Voice: tbd
    4. Voice: tbd
    """
    # TODO: build logic
    pass
