"""ChoraleBricks CSV data contract helpers.

The constants in this module define the v1.1 column layouts used by the
dataset conformance tests and by readers that validate ChoraleBricks CSV files.
Formatting helpers live here only when they are shared by generation or
migration scripts.
"""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


SCORE_FIELDS = [
    "start_meas",
    "end_meas",
    "start_quarter",
    "dur_quarter",
    "time_sig",
    "pitch_written",
    "pitch_written_name",
    "part",
    "instrument",
    "articulation",
    "expression",
    "dynamic",
    "tempo_qpm",
    "start_sec",
    "end_sec",
    "dur_sec",
    "midi_velocity",
]

ALIGNMENT_FIELDS = [
    "start_meas",
    "end_meas",
    "start_quarter",
    "dur_quarter",
    "time_sig",
    "pitch",
    "pitch_name",
    "pitch_written",
    "pitch_written_name",
    "part",
    "instrument",
    "articulation",
    "expression",
    "dynamic",
    "tempo_qpm",
    "start_sec",
    "end_sec",
    "dur_sec",
    "pitch_dev_cents",
    "midi_velocity",
]

NOTES_FIELDS = [
    "start_sec",
    "end_sec",
    "dur_sec",
    "pitch",
    "pitch_name",
    "pitch_written",
    "pitch_written_name",
    "pitch_dev_cents",
    "midi_velocity",
]

RAW_F0_FIELDS = ["t", "f0", "label"]
FILLED_F0_FIELDS = ["t", "f0"]
CHORD_FIELDS = ["start_meas", "end_meas", "chord"]

METADATA_SONG_FIELDS = ["song_id", "composer", "title", "year"]
METADATA_VIDEO_OFFSET_FIELDS = ["song_id", "offset"]
METADATA_TRACK_FIELDS = [
    "song_id",
    "part",
    "instrument",
    "path_audio",
    "path_f0",
    "path_notes",
    "date",
    "performer",
    "room",
    "microphone",
    "comments",
]
METADATA_PERFORMER_FIELDS = ["performer_id", "birthyear"]

ROOT_CSV_FIELDS = {
    "metadata_songs.csv": METADATA_SONG_FIELDS,
    "metadata_tracks.csv": METADATA_TRACK_FIELDS,
    "metadata_performers.csv": METADATA_PERFORMER_FIELDS,
    "metadata_video_offsets.csv": METADATA_VIDEO_OFFSET_FIELDS,
}

SCORE_PART_ORDER = {"S": 0, "A": 1, "T": 2, "B": 3}


INTEGER_STEP = Decimal("1")
MEASURE_BOUNDARY_OFFSET = 0.001
MEASURE_INTEGER_TOLERANCE = 1e-9
MIDI_VELOCITY_MIN = 0
MIDI_VELOCITY_MAX = 127

SECONDS_PATTERN = re.compile(r"^-?\d+\.\d{3}$")
INTEGER_PATTERN = re.compile(r"^-?\d+$")

def quantize_decimal(value: Any, step: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(step, rounding=ROUND_HALF_UP)


def format_measure_column_value(value: Any, exclusive_end: bool = False) -> str:
    """Format a measure position with three decimals.

    Exclusive end positions that land on an integer measure are shifted back by
    one millimeasure, for example ``1.000`` becomes ``0.999``.
    """
    numeric_value = float(value)
    if exclusive_end:
        nearest_integer = round(numeric_value)
        rounded_value = round(numeric_value, 3)
        rounded_integer = round(rounded_value)
        if math.isclose(
            numeric_value,
            nearest_integer,
            abs_tol=MEASURE_INTEGER_TOLERANCE,
        ):
            numeric_value = nearest_integer - MEASURE_BOUNDARY_OFFSET
        elif math.isclose(
            rounded_value,
            rounded_integer,
            abs_tol=MEASURE_INTEGER_TOLERANCE,
        ):
            numeric_value = rounded_integer - MEASURE_BOUNDARY_OFFSET

    sign = "-" if numeric_value < 0 else ""
    return f"{sign}{abs(numeric_value):.3f}"


def midi_velocity(value: Any) -> int:
    velocity = int(quantize_decimal(value, INTEGER_STEP))
    return max(MIDI_VELOCITY_MIN, min(MIDI_VELOCITY_MAX, velocity))


def velocity_from_scalar(value: Any) -> str:
    """Convert a [0, 1] loudness scalar to MIDI velocity in [0, 127]."""
    velocity = (Decimal(str(value)) * MIDI_VELOCITY_MAX).quantize(
        INTEGER_STEP,
        rounding=ROUND_HALF_UP,
    )
    return str(max(MIDI_VELOCITY_MIN, min(MIDI_VELOCITY_MAX, int(velocity))))
