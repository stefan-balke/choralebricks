import numpy as np
import pandas as pd
from pathlib import Path

from choralebricks.constants import Voices, VOICE_STRINGS


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
    if set(df.columns) != set(expected_columns):
        raise SchemaValidationError(
            f"Schema mismatch. Expected columns: {expected_columns}, but got: {list(df.columns)}"
        )


def read_f0(
    path_csv: Path,
    rename_cols: bool=True
) -> pd.DataFrame:
    expected_columns = ["TIME", "VALUE", "LABEL"]

    if path_csv == None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = pd.read_csv(path_csv, sep=",")
        try:
            validate_schema(df, expected_columns)
        except SchemaValidationError as e:
            print(f"Error: {e}")
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    # cosmetics
    if rename_cols:
        df = df.drop(columns=["LABEL"])
        df = df.rename(columns={
            "TIME": "t",
            "VALUE": "f0"
        })
    return df


def read_notes(
    path_csv: Path,
    A4: float=440.0,
    rename_cols: bool=True
) -> pd.DataFrame:
    expected_columns = ["TIME", "VALUE", "DURATION", "LEVEL", "LABEL"]

    if path_csv == None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = pd.read_csv(path_csv, sep=",")
        try:
            validate_schema(df, expected_columns)
        except SchemaValidationError as e:
            print(f"Error: {e}")
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    # cosmetics
    if rename_cols:
        df = df.drop(columns=["LEVEL", "LABEL"])
        df = df.rename(columns={
            "TIME": "t_start",
            "VALUE": "f0_mean",
            "DURATION": "t_dur"
        })

        df["pitch"] = (12 * (np.log2(df["f0_mean"].values) - np.log2(A4)) + 69)
        df["pitch"] = df["pitch"].round().astype(int)

    return df


def read_sheet_music_csv(
    path_csv: Path,
    A4: float=440.0
) -> pd.DataFrame:
    expected_columns = [
        "start_meas",
        "end_meas",
        "duration_quarterLength",
        "pitch",
        "pitchName",
        "timeSig",
        "articulation",
        "expression",
        "grace",
        "part",
        "midiChannel",
        "midiProgram",
        "volume",
        "pitchWritten",
        "pitchNameWritten",
        "quarternoteoffset",
        "quarterNoteBPM"
    ]

    if path_csv == None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = pd.read_csv(path_csv, sep=";")
        try:
            validate_schema(df, expected_columns)
        except SchemaValidationError as e:
            print(f"Error: {e}")
    else:
        raise FileNotFoundError(f"File not found: {path_csv}")

    df["dur_meas"] = df["end_meas"] - df["start_meas"]
    df["pitch_center_freq"] = A4 * 2**((df["pitch"] - 69) / 12)

    return df


def read_chords(path_csv: Path) -> pd.DataFrame:
    expected_columns = ['start_meas', 'end_meas', 'chord']

    if path_csv == None:
        raise FileNotFoundError(f"File not found: {path_csv}")

    if path_csv.exists():
        df = pd.read_csv(path_csv, sep=",")
        try:
            validate_schema(df, expected_columns)
        except SchemaValidationError as e:
            print(f"Error: {e}")
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
