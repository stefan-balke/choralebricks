import pandas as pd
from pathlib import Path


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
    A4: int=440,
    rename_cols: bool=True
) -> pd.DataFrame:
    expected_columns = ["TIME", "VALUE", "DURATION", "LEVEL", "LABEL"]

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

    return df
