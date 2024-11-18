import logging
from pathlib import Path
import pandas as pd
import soundfile as sf

from choralebricks.dataset import SongDB, EnsembleRandom, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()

    df_tracks = []

    # collect data for statistics
    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")

        for cur_track in cur_song.tracks:
            cur_track_wav_info = sf.info(cur_track.path_audio)

            cur_track_info = dict()
            cur_track_info["song_id"] = cur_track.song_id
            cur_track_info["voice"] = cur_track.voice
            cur_track_info["instrument"] = cur_track.instrument.value
            cur_track_info["instrument_type"] = cur_track.instrument_type.value
            cur_track_info["player_id"] = cur_track.player_id
            cur_track_info["audio_dur"] = cur_track_wav_info.duration

            df_tracks.append(cur_track_info)

    df_tracks = pd.DataFrame(df_tracks)

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
    print("Todo")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
