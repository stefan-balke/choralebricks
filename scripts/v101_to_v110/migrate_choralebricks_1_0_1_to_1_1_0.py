"""Migrate a ChoraleBricks 1.0.1 release to the 1.1 data contract."""

from __future__ import annotations

import argparse
import math
import shutil
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import tqdm

from choralebricks.constants import Instrument, INSTRUMENT_STRINGS
from choralebricks.format_spec_csv import format_measure_column_value, velocity_from_scalar


# Shared MEI music-theory lookups (used by the transposition helpers below).
MEI_NAMESPACE = "http://www.music-encoding.org/ns/mei"
MEI_TAG = f"{{{MEI_NAMESPACE}}}"
PITCH_CLASSES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
ACCIDENTAL_TO_OFFSET = {"ff": -2, "f": -1, "n": 0, "s": 1, "ss": 2}
OFFSET_TO_ACCIDENTAL = {value: key for key, value in ACCIDENTAL_TO_OFFSET.items()}
_MIDI_PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
TOP_LEVEL_COLUMNS_1_1 = [
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
ALIGNMENT_COLUMNS_1_1 = [
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
NOTES_COLUMNS_1_1 = [
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

SPECIAL_DOWN_OCTAVE_ROWS = {
    ("Jan_DuGrosserSchmerzensmann", "04_tb", "9.889"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.556"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "13.000"),
    ("Crueger_AufAufMeinHerzMitFreuden", "04_bcl", "10.333"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.000"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.889"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "11.889"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.667"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.222"),
    ("Crueger_AufAufMeinHerzMitFreuden", "04_bs", "11.222"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.333"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.833"),
    ("Vulpius_ChristusDerIstMeinLeben", "04_bs", "5.000"),
    ("Crueger_AufAufMeinHerzMitFreuden", "03_bcl", "12.500"),
}


def read_table(path: Path) -> pd.DataFrame:
    """Read a CSV as all-string columns, preserving values and empty cells verbatim."""
    rows = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False).fillna("")
    if rows.shape[1] == 1 and "," in rows.columns[0]:
        rows = pd.read_csv(path, sep=",", dtype=str, keep_default_na=False).fillna("")
    return rows


def write_table(frame: pd.DataFrame, path: Path) -> None:
    # Always use semicolon as the separator, no index column, and Unix line endings.
    frame.to_csv(path, sep=";", index=False, lineterminator="\n", encoding="utf-8")


def migrate_chord_csv(path: Path) -> None:
    df_chords = read_table(path)
    columns_actual = list(df_chords.columns)
    if columns_actual != ["start_meas", "end_meas", "chord"]:
        raise ValueError(f"{path}: unexpected chord CSV header {columns_actual}.")
    df_chords["start_meas"] = df_chords["start_meas"].map(format_measure_column_value)
    df_chords["end_meas"] = df_chords["end_meas"].map(
        lambda value: format_measure_column_value(value, exclusive_end=True)
    )
    write_table(df_chords, path)


def compute_end_times(starts, durations) -> list[str]:
    """Exact end time ``start + duration`` per row, kept as strings."""
    return [str(Decimal(start) + Decimal(dur)) for start, dur in zip(starts, durations)]


def format_three_decimals(value: str | Decimal) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.001')):.3f}"


def strip_numeric_leading_zeros(value: str) -> str:
    text = str(value)
    if text == "":
        return text
    decimal_value = Decimal(text)
    formatted = format(decimal_value, "f")
    if "." in formatted:
        integer, fraction = formatted.split(".", 1)
        integer = integer.lstrip("0") or "0"
        return f"{integer}.{fraction}"
    return formatted.lstrip("0") or "0"


def midi_to_pitch_name(midi: int) -> str:
    return f"{_MIDI_PITCH_NAMES[midi % 12]}{midi // 12 - 1}"


def sort_score_rows(frame: pd.DataFrame) -> pd.DataFrame:
    part_order = {"S": 0, "A": 1, "T": 2, "B": 3}
    keyed = frame.assign(
        _meas=frame["start_meas"].map(Decimal),
        _part=frame["part"].map(part_order),
    ).sort_values(["_meas", "_part"], kind="stable")
    return keyed.drop(columns=["_meas", "_part"])


def instrument_abbreviation_from_track_path(path: Path) -> str:
    stem = path.name.removesuffix("_notes.csv").removesuffix(".csv")
    try:
        _, instrument_code = stem.split("_", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: cannot infer instrument code from file name.") from exc
    return instrument_code


def song_id_from_track_path(path: Path) -> str:
    if path.parent.name == "annotations":
        return path.parent.parent.name
    return path.parent.name


def pitch_deviation_cents(f0_hz: float, pitch: str, a4: float = 440.0) -> str:
    if f0_hz <= 0.0:
        return ""
    reference_hz = a4 * 2 ** ((int(pitch) - 69) / 12)
    return str(round(1200 * math.log2(f0_hz / reference_hz)))


def performance_pitch(score_pitch: str, instrument: str, part: str = "") -> str:
    pitch = int(score_pitch)
    if instrument == "tba":
        pitch -= 12
    elif instrument == "fl":
        pitch += 12
    elif instrument == "bar" and part == "S":
        pitch -= 12
    return str(pitch)


def apply_special_pitch_corrections(
    df_alignment: pd.DataFrame,
    song_id: str,
    track_stem: str,
) -> pd.DataFrame:
    corrected = df_alignment.copy()
    for idx, row in corrected.iterrows():
        key = (song_id, track_stem, str(row["start_meas"]))
        if key not in SPECIAL_DOWN_OCTAVE_ROWS:
            continue
        midi = int(corrected.at[idx, "pitch"]) - 12
        corrected.at[idx, "pitch"] = str(midi)
        corrected.at[idx, "pitch_name"] = midi_to_pitch_name(midi)
    return corrected


def rows_by_part(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        part: part_rows.reset_index(drop=True)
        for part, part_rows in frame.groupby("part", sort=False)
    }


def migrate_notes_and_alignment_csvs(
    notes_path: Path,
    alignment_path: Path,
    raw_f0_cleaned: pd.DataFrame,
    score_rows: pd.DataFrame,
) -> None:
    df_notes = read_table(notes_path)
    df_alignment = read_table(alignment_path)
    if list(df_notes.columns) != ["TIME", "VALUE", "DURATION", "LEVEL", "LABEL"]:
        raise ValueError(f"{notes_path}: unexpected notes header in v1.0.1: {list(df_notes.columns)}.")
    if list(df_alignment.columns) != [
        "t_start", "f0_mean", "t_dur", "pitch_audio", "start_meas", "end_meas",
        "duration_quarterLength", "pitch_sheet_music", "pitchName", "timeSig", "part",
    ]:
        raise ValueError(f"{alignment_path}: unexpected alignment header in v1.0.1: {list(df_alignment.columns)}.")
    if len(df_notes) != len(df_alignment):
        raise ValueError(f"{notes_path}: {len(df_notes)} notes do not match {len(df_alignment)} alignment rows.")

    song_id = song_id_from_track_path(notes_path)
    track_stem = notes_path.name.removesuffix("_notes.csv")
    instrument = instrument_abbreviation_from_track_path(notes_path)
    part = df_alignment["part"].iloc[0]
    if not (df_alignment["part"] == part).all():
        raise ValueError(f"{alignment_path}: expected exactly one part per track alignment.")
    score_part_rows = rows_by_part(score_rows).get(part)
    if score_part_rows is None:
        raise ValueError(f"{alignment_path}: no top-level score rows found for part {part}.")
    if len(score_part_rows) != len(df_alignment):
        raise ValueError(
            f"{alignment_path}: {len(df_alignment)} alignment rows do not match "
            f"{len(score_part_rows)} top-level score rows for part {part}."
        )

    raw_t = raw_f0_cleaned["t"].astype(float)
    raw_f0 = raw_f0_cleaned["f0"].astype(float)
    note_starts = df_notes["TIME"].astype(float)
    note_ends = note_starts + df_notes["DURATION"].astype(float)

    def note_f0_median(start: float, end: float) -> float:
        in_window = raw_f0[(raw_t >= start) & (raw_t <= end) & (raw_f0 != 0.0)]
        return float(in_window.median()) if len(in_window) > 0 else 0.0

    f0_medians = [note_f0_median(s, e) for s, e in zip(note_starts, note_ends)]
    midi_velocity = df_notes["LEVEL"].map(velocity_from_scalar)
    start_sec = df_notes["TIME"]
    dur_sec = df_notes["DURATION"]
    end_sec = compute_end_times(start_sec, dur_sec)

    df_alignment["pitch_written"] = df_alignment["pitch_sheet_music"].map(str)
    df_alignment = df_alignment.drop(columns=["f0_mean", "pitch_audio"])
    df_alignment = df_alignment.rename(columns={
        "duration_quarterLength": "dur_quarter",
        "pitch_sheet_music": "pitch",
        "pitchName": "pitch_name",
        "timeSig": "time_sig",
        "t_start": "start_sec",
        "t_dur": "dur_sec",
    })
    df_alignment["pitch_name"] = df_alignment["pitch_name"].str.replace("-", "b", regex=False)

    df_alignment["start_meas"] = df_alignment["start_meas"].map(format_measure_column_value)
    df_alignment["end_meas"] = df_alignment["end_meas"].map(
        lambda value: format_measure_column_value(value, exclusive_end=True)
    )
    df_alignment["dur_quarter"] = df_alignment["dur_quarter"].map(strip_numeric_leading_zeros)
    df_alignment["pitch"] = [performance_pitch(p, instrument, part) for p in df_alignment["pitch"]]
    df_alignment = apply_special_pitch_corrections(df_alignment, song_id, track_stem)
    df_alignment["pitch_name"] = [midi_to_pitch_name(int(pitch)) for pitch in df_alignment["pitch"]]

    pitch_dev_cents = [
        pitch_deviation_cents(f0, pitch)
        for f0, pitch in zip(f0_medians, df_alignment["pitch"])
    ]

    df_alignment["start_quarter"] = score_part_rows["start_quarter"].to_numpy()
    df_alignment["pitch_written_name"] = score_part_rows["pitch_written_name"].to_numpy()
    df_alignment["instrument"] = INSTRUMENT_STRINGS[Instrument(instrument)]
    df_alignment["articulation"] = score_part_rows["articulation"].to_numpy()
    df_alignment["expression"] = score_part_rows["expression"].to_numpy()
    df_alignment["dynamic"] = ""
    df_alignment["tempo_qpm"] = score_part_rows["tempo_qpm"].to_numpy()
    df_alignment["start_sec"] = start_sec.map(format_three_decimals).to_numpy()
    df_alignment["end_sec"] = [format_three_decimals(value) for value in end_sec]
    df_alignment["dur_sec"] = dur_sec.map(format_three_decimals).to_numpy()
    df_alignment["pitch_dev_cents"] = pitch_dev_cents
    df_alignment["midi_velocity"] = midi_velocity.to_numpy()
    df_alignment = df_alignment[ALIGNMENT_COLUMNS_1_1]
    df_notes = df_alignment[NOTES_COLUMNS_1_1]

    write_table(df_notes, notes_path)
    write_table(df_alignment, alignment_path)


def migrate_top_level_csv(path: Path) -> None:
    df_top_level = read_table(path)
    columns_actual = list(df_top_level.columns)
    columns_1_0 = [
        "start_meas", "end_meas", "duration_quarterLength", "pitch", "pitchName",
        "timeSig", "articulation", "expression", "grace", "part", "midiChannel",
        "midiProgram", "volume", "pitchWritten", "pitchNameWritten",
        "quarternoteoffset", "quarterNoteBPM",
    ]
    columns_1_1_order = [
        *TOP_LEVEL_COLUMNS_1_1,
        "midiChannel",
    ]
    if columns_actual != columns_1_0:
        raise ValueError(f"{path}: unexpected top-level CSV header {columns_actual}.")

    df_top_level = df_top_level.rename(
        columns={
            "duration_quarterLength": "dur_quarter",
            "pitch": "pitch_written",
            "pitchName": "pitch_written_name",
            "timeSig": "time_sig",
            "volume": "midi_velocity",
            "quarternoteoffset": "start_quarter",
            "quarterNoteBPM": "tempo_qpm",
        }
    )
    df_top_level = df_top_level.drop(columns=["grace", "midiProgram", "pitchWritten", "pitchNameWritten"])
    df_top_level["pitch_written_name"] = df_top_level["pitch_written_name"].str.replace("-", "b", regex=False)
    
    df_top_level["start_meas"] = df_top_level["start_meas"].map(format_measure_column_value)
    df_top_level["end_meas"] = df_top_level["end_meas"].map(lambda value: format_measure_column_value(value, exclusive_end=True))
    df_top_level["start_quarter"] = df_top_level["start_quarter"].map(strip_numeric_leading_zeros)
    df_top_level["dur_quarter"] = df_top_level["dur_quarter"].map(strip_numeric_leading_zeros)
    df_top_level["instrument"] = ""
    df_top_level["dynamic"] = ""
    df_top_level["start_sec"] = ""
    df_top_level["end_sec"] = ""
    df_top_level["dur_sec"] = ""
    df_top_level["midi_velocity"] = df_top_level["midi_velocity"].map(velocity_from_scalar)
    df_top_level = df_top_level[columns_1_1_order]

    df_top_level_sorted = sort_score_rows(df_top_level)
    df_top_level_sorted = df_top_level_sorted[TOP_LEVEL_COLUMNS_1_1]
    write_table(df_top_level_sorted, path)


def clean_f0_annotations(
    notes_path: Path,
    raw_path: Path,
    filled_path: Path,
) -> pd.DataFrame:
    """Remove raw F0 values outside note events, zero filled F0 outside note events.

    Returns the cleaned raw F0 DataFrame (columns: t, f0, label) for downstream use.
    """
    notes = read_table(notes_path)
    if list(notes.columns) != ["TIME", "VALUE", "DURATION", "LEVEL", "LABEL"]:
        raise ValueError(f"{notes_path}: unexpected notes header {list(notes.columns)}.")
    raw = read_table(raw_path)
    if list(raw.columns) != ["TIME", "VALUE", "LABEL"]:
        raise ValueError(f"{raw_path}: unexpected raw F0 header {list(raw.columns)}.")
    raw = raw.rename(columns={"TIME": "t", "VALUE": "f0", "LABEL": "label"})

    filled = read_table(filled_path)
    if list(filled.columns) != ["t", "f0"]:
        raise ValueError(f"{filled_path}: unexpected filled F0 header {list(filled.columns)}.")

    starts = notes["TIME"].astype(float).to_numpy()
    ends = starts + notes["DURATION"].astype(float).to_numpy()

    def in_any_note(times: pd.Series) -> pd.Series:
        flags = [bool(((starts <= t) & (t <= ends)).any()) for t in times.astype(float)]
        return pd.Series(flags, index=times.index)

    raw_keep = (raw["f0"].astype(float) != 0) & in_any_note(raw["t"])
    cleaned_raw = raw[raw_keep].reset_index(drop=True)
    write_table(cleaned_raw, raw_path)

    outside = (filled["f0"].astype(float) != 0) & ~in_any_note(filled["t"])
    filled.loc[outside, "f0"] = "0.0"
    write_table(filled, filled_path)
    return cleaned_raw


def replace_known_bad_04_bar_f0_annotations(target: Path) -> None:
    """Replace a known copied F0 artifact with the checked-in corrected pitch track."""
    annotations_dir = (
        target
        / "01_AudioAndAnnotations"
        / "Vulpius_ChristusDerIstMeinLeben"
        / "annotations"
    )
    raw_path = annotations_dir / "04_bar_f0.csv"
    filled_path = annotations_dir / "04_bar_f0_filled.csv"
    replacement_svl = Path(__file__).resolve().parent / "04_bar.svl"

    if not replacement_svl.is_file():
        raise FileNotFoundError(
            f"Expected replacement Sonic Visualiser file not found: {replacement_svl}."
        )

    root = ET.parse(replacement_svl).getroot()
    model = root.find(".//model")
    if model is None:
        raise ValueError(f"{replacement_svl}: missing <model> definition.")
    sample_rate = float(model.attrib["sampleRate"])
    points = root.findall(".//point")
    if not points:
        raise ValueError(f"{replacement_svl}: no pitch points found.")
    raw_pitch = pd.DataFrame({
        "TIME": [float(p.attrib["frame"]) / sample_rate for p in points],
        "VALUE": [float(p.attrib["value"]) for p in points],
        "LABEL": [p.attrib.get("label", "") for p in points],
    })

    filled_template = read_table(filled_path)
    if list(filled_template.columns) != ["t", "f0"]:
        raise ValueError(f"{filled_path}: unexpected filled F0 header {list(filled_template.columns)}.")
    target_times = filled_template["t"].astype(float).to_numpy()
    f0_orig = raw_pitch[["TIME", "VALUE"]].astype(float).to_numpy()
    _, unique_idx = np.unique(f0_orig[:, 0], return_index=True)
    f0_orig = f0_orig[np.sort(unique_idx)]
    f0_new = (
        np.interp(target_times, f0_orig[:, 0], f0_orig[:, 1], left=0.0, right=0.0)
        if len(f0_orig) >= 2
        else np.zeros_like(target_times)
    )
    filled_pitch = pd.DataFrame({"t": filled_template["t"].to_numpy(), "f0": f0_new})

    write_table(raw_pitch, raw_path)
    write_table(filled_pitch, filled_path)


def mei_note_midi(note: ET.Element, key_offsets: dict[str, int]) -> int:
    pname = note.attrib["pname"]
    accidental = key_offsets.get(pname, 0)
    for child in note:
        if child.tag == f"{MEI_TAG}accid":
            encoded = child.attrib.get("accid.ges") or child.attrib.get("accid")
            if encoded:
                accidental = ACCIDENTAL_TO_OFFSET[encoded]
    return (int(note.attrib["oct"]) + 1) * 12 + PITCH_CLASSES[pname] + accidental


def target_spelling(source_pname: str, target_midi: int) -> tuple[str, int, int]:
    previous_diatonic = {
        "c": "b", "d": "c", "e": "d", "f": "e", "g": "f", "a": "g", "b": "a",
    }
    pname = previous_diatonic[source_pname]
    candidates = []
    for octave in range(0, 9):
        natural_midi = (octave + 1) * 12 + PITCH_CLASSES[pname]
        alteration = target_midi - natural_midi
        if alteration in OFFSET_TO_ACCIDENTAL:
            candidates.append((abs(alteration), pname, octave, alteration))
    if not candidates:
        raise ValueError(f"Cannot spell MIDI pitch {target_midi} from {source_pname}.")
    _, pname, octave, alteration = min(candidates)
    return pname, octave, alteration


def transpose_crueger_mei(mei_path: Path) -> int:
    source_key_offsets = {"f": 1, "c": 1}
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(mei_path, parser=parser)
    root = tree.getroot()
    score_defs = [
        score_def
        for score_def in root.iter(f"{MEI_TAG}scoreDef")
        if "key.pname" in score_def.attrib or "keysig" in score_def.attrib
    ]
    if len(score_defs) != 1:
        raise ValueError(
            f"{mei_path}: expected one keyed scoreDef, found {len(score_defs)}."
        )
    score_def = score_defs[0]
    if (
        score_def.attrib.get("keysig") != "2s"
        or score_def.attrib.get("key.pname") != "d"
        or score_def.attrib.get("key.mode") != "major"
    ):
        raise ValueError(f"{mei_path}: expected a D-major score definition.")
    score_def.attrib.pop("keysig")
    score_def.attrib["key.pname"] = "c"

    changed = 0
    for note in root.iter(f"{MEI_TAG}note"):
        if "pname" not in note.attrib or "oct" not in note.attrib:
            continue
        source_midi = mei_note_midi(note, source_key_offsets)
        target_midi = source_midi - 2
        pname, octave, alteration = target_spelling(
            note.attrib["pname"],
            target_midi,
        )
        note.attrib["pname"] = pname
        note.attrib["oct"] = str(octave)

        accidental_nodes = [
            child for child in note if child.tag == f"{MEI_TAG}accid"
        ]
        if alteration == 0:
            for child in accidental_nodes:
                note.remove(child)
        else:
            accidental = (
                accidental_nodes[0]
                if accidental_nodes
                else ET.SubElement(note, f"{MEI_TAG}accid")
            )
            accidental.attrib.clear()
            accidental.attrib["accid.ges"] = OFFSET_TO_ACCIDENTAL[alteration]
            for child in accidental_nodes[1:]:
                note.remove(child)

        if mei_note_midi(note, {}) != target_midi:
            raise RuntimeError(f"{mei_path}: failed to transpose a note.")
        changed += 1

    ET.register_namespace("", MEI_NAMESPACE)
    tree.write(mei_path, encoding="utf-8", xml_declaration=True)
    return changed


VOICE_TO_PART = {"1": "S", "2": "A", "3": "T", "4": "B"}


def migrate_metadata_tracks_csv(path: Path) -> None:
    df = read_table(path)
    if list(df.columns[:3]) != ["song_id", "voice", "instrument"]:
        raise ValueError(f"{path}: unexpected metadata_tracks header in v1.0.1: {list(df.columns)}.")
    df = df.rename(columns={"voice": "part"})
    df["part"] = df["part"].map(VOICE_TO_PART)
    df["instrument"] = df["instrument"].map(lambda abbr: INSTRUMENT_STRINGS[Instrument(abbr)])
    write_table(df, path)


def migrate_release(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"Source release directorynot found: {source}.")
    if target.exists():
        raise FileExistsError(f"Target directory already exists: {target}.")

    # copy the entire dataset into a new directory, then migrate in-place
    shutil.copytree(source, target, copy_function=shutil.copy2)

    audio_root = target / "01_AudioAndAnnotations"
    video_root = target / "02_ConductingVideos"

    # 1. Remove the orphan file 03_bcl_notes.csv in the piece Gesius_DuFriedensfuerstHerrJesuChrist
    # before collecting note paths, otherwise the stale source file skews the count.
    orphan = target / (
        "01_AudioAndAnnotations/Gesius_DuFriedensfuerstHerrJesuChrist"
        "/annotations/03_eh_notes.csv"
    )
    if not orphan.is_file():
        shutil.rmtree(target)
        raise FileNotFoundError(f"Expected stale orphan file not found: {orphan}.")
    orphan.unlink()

    alignment_csv_paths = sorted(audio_root.rglob("**/alignments/*.csv"))
    notes_csv_paths = sorted(audio_root.rglob("**/*_notes.csv"))
    if len(alignment_csv_paths) != 193 or len(notes_csv_paths) != 193:
        shutil.rmtree(target)
        raise RuntimeError(
            f"Expected 193 alignments and notes, found "
            f"{len(alignment_csv_paths)} and {len(notes_csv_paths)}."
        )
    
    try:
        # 2. Migrate metadata_tracks.csv: voice (1-4) → part (SATB), instrument abbreviation → full name
        migrate_metadata_tracks_csv(audio_root / "metadata_tracks.csv")

        # 3. Replace known bad F0 annotations (copy-paste error in v1.0.1)
        replace_known_bad_04_bar_f0_annotations(target)

        # 4. Mandatory VERSION tagging starting from v1.1.0
        for dir in (audio_root, video_root):
            (dir / "VERSION").write_text("1.1.0\n", encoding="utf-8")

        # 5. The piece Crueger_AufAufMeinHerzMitFreuden is notated in D major but should be in C major to match the rest of the dataset. 
        # We transpose it down 2 semitones by editing the MEI file.
        crueger = "Crueger_AufAufMeinHerzMitFreuden"
        transpose_crueger_mei(audio_root / crueger / f"{crueger}.mei")

        # 6. Migrate per-chorale top-level csv
        score_rows_by_chorale: dict[Path, pd.DataFrame] = {}
        for chorale_dir in sorted(path for path in audio_root.iterdir() if path.is_dir()):
            chord_path = chorale_dir / "annotations" / "chords.csv"
            if chord_path.is_file():
                migrate_chord_csv(chord_path)
            for path in sorted(chorale_dir.glob("*.csv")):
                migrate_top_level_csv(path)
                score_rows_by_chorale[chorale_dir] = read_table(path)

        # 7. Migrate per-chorale note and alignment CSVs
        for notes_csv_path in tqdm.tqdm(notes_csv_paths, desc="Migrating ChoraleBricks v1.0.1 to v1.1.0"):
            chorale_dir = notes_csv_path.parent.parent
            score_rows = score_rows_by_chorale.get(chorale_dir)
            if score_rows is None:
                raise ValueError(f"{chorale_dir}: no migrated top-level score CSV found.")
            alignment_csv_path = (
                chorale_dir
                / "alignments"
                / notes_csv_path.name.replace("_notes.csv", ".csv")
            )
            stem = notes_csv_path.name.removesuffix("_notes.csv")
            raw_path = notes_csv_path.with_name(f"{stem}_f0.csv")
            f0_filled_path = notes_csv_path.with_name(f"{stem}_f0_filled.csv")
            f0_raw_cleaned = clean_f0_annotations(notes_csv_path, raw_path, f0_filled_path)
            migrate_notes_and_alignment_csvs(notes_csv_path, alignment_csv_path, f0_raw_cleaned, score_rows)

    except Exception:
        # If any migration step fails, abort.
        shutil.rmtree(target)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path(r"C:\datasets\choralebricks\1.0.1")
    )
    parser.add_argument(
        "--target", type=Path, default=Path(r"C:\datasets\choralebricks\1.1.0")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    migrate_release(args.source, args.target)
    print(f"Migrated ChoraleBricks {args.source} to {args.target}.")


if __name__ == "__main__":
    main()
