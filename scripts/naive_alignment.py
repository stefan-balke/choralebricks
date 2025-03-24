"""
This script aligns the notes from the audio file to the sheet music by a naive 1-1 mapping.
"""
import numpy as np
from pathlib import Path
import logging

from choralebricks.generators import tracks
from choralebricks.utils import read_notes, read_sheet_music_csv, voice_to_name


logging.basicConfig(
    filename="scripts/naive_alignment.log",  # Log file name
    level=logging.DEBUG,  # Log all levels to the file
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",  # Clear the log file at the start
)

def main():
    out_folder = Path("scripts/alignments")
    out_folder.mkdir(parents=True, exist_ok=True)
    cur_track = list(tracks())[0]

    # iterate over all available tracks and get the path to the audio file
    for cur_track in list(tracks()):

        cur_sheet_music = read_sheet_music_csv(cur_track.path_sheet_music_csv)
        try:
            cur_sheet_music = read_sheet_music_csv(cur_track.path_sheet_music_csv)
            cur_sheet_music = cur_sheet_music.sort_values("start_meas")
            cur_notes = read_notes(cur_track.path_notes)
            cur_notes = cur_notes.sort_values("t_start")

            # get midi pitches from mean f0
            cur_notes["pitch"] = 12 * (np.log2(np.asanyarray(cur_notes["f0_mean"])) - np.log2(440.0)) + 69
            cur_notes["pitch"] = cur_notes["pitch"].round().astype("int")

            # filter sheet music to voice
            cur_voice_name = voice_to_name(cur_track.voice)
            cur_sheet_music = cur_sheet_music[cur_sheet_music["part"] == cur_voice_name]

            # Check if the number of note events is equal
            try:
                assert cur_sheet_music.shape[0] == cur_notes.shape[0]
            except AssertionError:
                print(f"Found #notes problem in {cur_track.song_id} -> {cur_track.path_audio.name}")
                print(cur_sheet_music.shape, cur_notes.shape)

            # naive alignment by 1-1 mapping
            cur_notes["start_meas"] = cur_sheet_music["start_meas"].values
            cur_notes["end_meas"] = cur_sheet_music["end_meas"].values
            cur_notes["duration_quarterLength"] = cur_sheet_music["duration_quarterLength"].values
            cur_notes["pitch_sheet_music"] = cur_sheet_music["pitch"].values
            cur_notes["pitchName"] = cur_sheet_music["pitchName"].values
            cur_notes["timeSig"] = cur_sheet_music["timeSig"].values
            cur_notes["part"] = cur_sheet_music["part"].values

            # Check if pitches are the same for every note
            if not any(cur_notes["pitch"].values == cur_sheet_music["pitch"].values):
                logging.info(f"Found pitch problem in {cur_track.song_id} -> {cur_track.path_audio.name}")
                logging.info(cur_notes)

                if any(abs(cur_notes["pitch"].values - cur_sheet_music["pitch"].values) == 12):
                    logging.info("Only octave deltas.")
                else:
                    logging.info(f"Skipping {cur_track.path_audio.stem}...")
                    continue

            cur_notes = cur_notes.rename(columns={"pitch": "pitch_audio"})

            song_folder = out_folder / cur_track.song_id / "alignments"
            song_folder.mkdir(parents=True, exist_ok=True)

            cur_notes.to_csv(
                song_folder / f"{cur_track.path_audio.stem}.csv",
                sep=";",
                index=False
            )


        except FileNotFoundError:
            continue


if __name__ == "__main__":
    main()
