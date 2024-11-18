import logging
from pathlib import Path
import pandas as pd
import soundfile as sf

from choralebricks.dataset import SongDB, EnsemblePermutations

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()

    df_songs = []
    df_tracks = []

    # collect data for statistics
    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")

        cur_song_info = dict()
        cur_song_info["song_id"] = cur_song.id

        # get the permutations
        cur_ensembles = EnsemblePermutations(cur_song)
        cur_song_info["n_permutations"] = len(cur_ensembles)

        cur_track_durs = list()

        for cur_track in cur_song.tracks:
            cur_track_wav_info = sf.info(cur_track.path_audio)

            cur_track_info = dict()
            cur_track_info["song_id"] = cur_track.song_id
            cur_track_info["voice"] = cur_track.voice
            cur_track_info["instrument"] = cur_track.instrument.value
            cur_track_info["instrument_type"] = cur_track.instrument_type.value
            cur_track_info["player_id"] = cur_track.player_id
            cur_track_info["audio_dur"] = cur_track_wav_info.duration
            cur_track_durs.append(cur_track_wav_info.duration)

            df_tracks.append(cur_track_info)

        cur_song_info["min_dur"] = min(cur_track_durs)
        df_songs.append(cur_song_info)

    df_tracks = pd.DataFrame(df_tracks)
    df_songs = pd.DataFrame(df_songs)

    print(u"\u2500" * 40)
    print(f"#Songs: {df_tracks["song_id"].nunique()}")
    print(f"#Tracks: {df_tracks.shape[0]}")
    print(u"\u2500" * 40)

    print(u"\u2500" * 40)
    print("#Tracks per Song")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("song_id").size())

    print(u"\u2500" * 40)
    print("#Tracks per Voice")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("voice").size())

    print(u"\u2500" * 40)
    print("#Tracks per Instrument Type")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("instrument_type").agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
        )
    )

    print(u"\u2500" * 40)
    print("#Tracks per Instrument")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("instrument").agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
        )
    )

    print(u"\u2500" * 40)
    print("#Ensembles per Song")
    print(u"\u2500" * 40)
    df_songs["perm_dur"] = df_songs["n_permutations"] * df_songs["min_dur"]
    df_songs["perm_dur"] = pd.to_datetime(df_songs["perm_dur"], unit='s').dt.strftime('%H:%M:%S')
    print(df_songs.sort_values("song_id"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
