import numpy as np
import pandas as pd
from pathlib import Path

from choralebricks.constants import A4_REFERENCE_HZ, Voices, VOICE_STRINGS
from choralebricks.format_spec_csv import (
    CHORD_FIELDS,
    FILLED_F0_FIELDS,
    NOTES_FIELDS,
    RAW_F0_FIELDS,
    SCORE_FIELDS,
)


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    def __init__(
            self,
            message="The schema of the file does not match the expected format"
        ):
        super().__init__(message)

def validate_schema(
        df,
        expected_columns
    ):
    """Validate if the DataFrame schema matches the expected columns."""
    if list(df.columns) != list(expected_columns):
        raise SchemaValidationError(
            f"Schema mismatch. Expected columns: {expected_columns}, but got: {list(df.columns)}"
        )


def read_validated_csv(path_csv: Path, expected_columns) -> pd.DataFrame:
    """Read a semicolon-delimited CSV and validate its header.

    ChoraleBricks v1.1 CSVs are semicolon-delimited; a header mismatch raises
    ``SchemaValidationError``.
    """
    df = pd.read_csv(path_csv, sep=";")
    validate_schema(df, expected_columns)
    return df


def read_f0_sv(
    path_csv: Path,
    rename_cols: bool=True
) -> pd.DataFrame:
    if path_csv is None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = read_validated_csv(path_csv, RAW_F0_FIELDS)
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if rename_cols:
        df = df.drop(columns=["label"])
    return df


def read_f0(
    path_csv: Path,
) -> pd.DataFrame:
    if path_csv is None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = read_validated_csv(path_csv, FILLED_F0_FIELDS)
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    return df


def read_notes(
    path_csv: Path,
    rename_cols: bool=True
) -> pd.DataFrame:
    if path_csv is None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = read_validated_csv(path_csv, NOTES_FIELDS)
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    return df


def read_sheet_music_csv(
    path_csv: Path,
    A4: float=A4_REFERENCE_HZ
) -> pd.DataFrame:
    if path_csv is None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = read_validated_csv(path_csv, SCORE_FIELDS)
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    df["dur_meas"] = df["end_meas"] - df["start_meas"]
    df["pitch_center_freq"] = A4 * 2**((df["pitch_written"] - 69) / 12)

    return df


def read_chords(path_csv: Path) -> pd.DataFrame:
    if path_csv is None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = read_validated_csv(path_csv, CHORD_FIELDS)
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    return df


def voice_to_name(voice_value: int) -> str:
    # Mapping from Voices enum to strings
    try:
        voice_enum = Voices(voice_value)  # Convert value to enum
        return VOICE_STRINGS[voice_enum]  # Get the corresponding string
    except (ValueError, KeyError):
        return "Unknown"  # Handle invalid values


def get_voice_from_int(value):
    try:
        return Voices(value)
    except ValueError:
        return None


def midi2hz(p, f_ref=440):
    """ Returns center frequency in Hz for a given (optionally fractional) MIDI pitch
    """
    return f_ref * np.power(2, (p - 69) / 12)

def hz2midi(f, f_ref=440):
    """ Returns (optionally fractional) MIDI pitch for a given frequency in Hz
    """
    return np.log2(f/f_ref) * 12 + 69
