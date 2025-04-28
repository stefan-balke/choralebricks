"""
Script to collect metadata for all tracks in the dataset.
"""
import pandas as pd
from pathlib import Path

from choralebricks.dataset import SongDB


def main():
    cbdb = SongDB()
    print(cbdb.songs)
    ROOT_RAW = Path("/Users/stefan/dev/chorale_bricks/data/01_raw")

    df_meta = []

    for cur_song in cbdb.songs:
        cur_df_meta = []
        for cur_track in cur_song.tracks:
            cur_meta = {
                "song_id": cur_song.id,
                "voice": cur_track.voice,
                "instrument": cur_track.instrument.value,
                "path_audio": cur_track.path_audio.name,
                "path_f0": cur_track.path_f0.name,
                "path_notes": cur_track.path_notes.name
            }
            cur_df_meta.append(cur_meta)
        cur_df_meta = pd.DataFrame(cur_df_meta)

        # merge with existing metadata
        df_old_meta = pd.read_csv(ROOT_RAW / cur_song.id / "metadata_tracks.csv", sep=";")
        df_old_meta.rename(columns={"instrument_id": "instrument"}, inplace=True)
        df_old_meta.rename(columns={"part": "voice"}, inplace=True)
        print(df_old_meta)
        cur_df_meta = pd.merge(cur_df_meta, df_old_meta, on=["voice", "instrument"], how="left")
        df_meta.append(cur_df_meta)

    df_meta = pd.concat(df_meta, ignore_index=True)
    df_meta.sort_values(
        by=["song_id", "voice", "instrument"],
        inplace=True
    )
    print(df_meta)
    df_meta.to_csv(
        ROOT_RAW / "metadata_tracks.csv",
        sep=";",
        index=False
    )

if __name__ == "__main__":
    # main()
    df_meta = pd.read_csv(
        "/Users/stefan/dev/chorale_bricks/data/02_multitrack/metadata_tracks.csv",
        sep=";"
    )
    print(df_meta.groupby("song_id").size())
