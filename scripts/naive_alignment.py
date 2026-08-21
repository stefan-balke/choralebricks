"""
This script aligns the notes from the audio file to the sheet music by a naive 1-1 mapping.
"""
from pathlib import Path
import logging

import pandas as pd

from choralebricks.constants import INSTRUMENT_STRINGS
from choralebricks.format_spec_csv import ALIGNMENT_FIELDS
from choralebricks.generators import tracks
from choralebricks.utils import read_notes, read_sheet_music_csv


logging.basicConfig(
    filename="scripts/naive_alignment.log",  # Log file name
    level=logging.DEBUG,  # Log all levels to the file
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",  # Clear the log file at the start
)

ALIGNMENT_DECIMALS = {
    "start_meas": 3,
    "end_meas": 3,
    "start_quarter": 3,
    "dur_quarter": 1,
    "tempo_qpm": 3,
    "start_sec": 3,
    "end_sec": 3,
    "dur_sec": 3,
    "pitch": 0,
    "pitch_written": 0,
    "pitch_dev_cents": 0,
    "midi_velocity": 0,
}


def format_number(value, decimals):
    """Render a numeric cell the way the dataset CSVs do, blanks included."""
    if pd.isna(value):
        return ""

    return f"{value:.{decimals}f}"


def main():
    out_folder = Path("scripts/alignments")
    out_folder.mkdir(parents=True, exist_ok=True)

    # iterate over all available tracks and get the path to the audio file
    for cur_track in list(tracks()):

        try:
            cur_sheet_music = read_sheet_music_csv(cur_track.path_sheet_music_csv)
            cur_sheet_music = cur_sheet_music.sort_values("start_meas")
            cur_notes = read_notes(cur_track.path_notes)
            cur_notes = cur_notes.sort_values("start_sec")

            # filter sheet music to part
            cur_sheet_music = cur_sheet_music[cur_sheet_music["part"] == cur_track.part]

            # Check if the number of note events is equal. A 1-1 mapping is
            # impossible otherwise, so skip instead of failing further down.
            if cur_sheet_music.shape[0] != cur_notes.shape[0]:
                print(f"Found #notes problem in {cur_track.song_id} -> {cur_track.path_audio.name}")
                print(cur_sheet_music.shape, cur_notes.shape)
                continue

            # Check if pitches are the same for every note. Compare written
            # against written, so transposing instruments do not register as a
            # mismatch (`pitch` is the sounding pitch).
            pitch_delta = (
                cur_notes["pitch_written"].values
                - cur_sheet_music["pitch_written"].values
            )
            if not all(pitch_delta == 0):
                logging.info(f"Found pitch problem in {cur_track.song_id} -> {cur_track.path_audio.name}")
                logging.info(cur_notes)

                if all(abs(pitch_delta[pitch_delta != 0]) == 12):
                    logging.info("Only octave deltas.")
                else:
                    logging.info(f"Skipping {cur_track.path_audio.stem}...")
                    continue

            # naive alignment by 1-1 mapping: symbolic columns come from the
            # score, everything measured from the audio comes from the notes.
            cur_alignment = pd.DataFrame({
                "start_meas": cur_sheet_music["start_meas"].values,
                "end_meas": cur_sheet_music["end_meas"].values,
                "start_quarter": cur_sheet_music["start_quarter"].values,
                "dur_quarter": cur_sheet_music["dur_quarter"].values,
                "time_sig": cur_sheet_music["time_sig"].values,
                "pitch": cur_notes["pitch"].values,
                "pitch_name": cur_notes["pitch_name"].values,
                "pitch_written": cur_sheet_music["pitch_written"].values,
                "pitch_written_name": cur_sheet_music["pitch_written_name"].values,
                "part": cur_sheet_music["part"].values,
                "instrument": INSTRUMENT_STRINGS[cur_track.instrument],
                "articulation": cur_sheet_music["articulation"].values,
                "expression": cur_sheet_music["expression"].values,
                "dynamic": cur_sheet_music["dynamic"].values,
                "tempo_qpm": cur_sheet_music["tempo_qpm"].values,
                "start_sec": cur_notes["start_sec"].values,
                "end_sec": cur_notes["end_sec"].values,
                "dur_sec": cur_notes["dur_sec"].values,
                "pitch_dev_cents": cur_notes["pitch_dev_cents"].values,
                "midi_velocity": cur_notes["midi_velocity"].values,
            })[ALIGNMENT_FIELDS]

            for cur_col, cur_decimals in ALIGNMENT_DECIMALS.items():
                cur_alignment[cur_col] = cur_alignment[cur_col].map(
                    lambda value, d=cur_decimals: format_number(value, d)
                )

            song_folder = out_folder / cur_track.song_id / "alignments"
            song_folder.mkdir(parents=True, exist_ok=True)

            cur_alignment.to_csv(
                song_folder / f"{cur_track.path_audio.stem}.csv",
                sep=";",
                index=False
            )


        except FileNotFoundError:
            continue


if __name__ == "__main__":
    main()
