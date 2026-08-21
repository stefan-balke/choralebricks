import csv
import re
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from choralebricks import format_spec_csv as spec
from choralebricks.dataset import EnsemblePermutations, SongDB
from choralebricks.utils import read_f0_sv, read_notes
from choralebricks import ChordSequence


ALIGNMENT_FIELDS = spec.ALIGNMENT_FIELDS
NOTES_FIELDS = spec.NOTES_FIELDS
RAW_F0_FIELDS = spec.RAW_F0_FIELDS
FILLED_F0_FIELDS = spec.FILLED_F0_FIELDS
SCORE_FIELDS = spec.SCORE_FIELDS
SCORE_PART_ORDER = spec.SCORE_PART_ORDER
CHORD_FIELDS = spec.CHORD_FIELDS
ROOT_CSV_FIELDS = spec.ROOT_CSV_FIELDS
ALIGNMENT_SCORE_FIELDS = [
    "start_meas",
    "end_meas",
    "start_quarter",
    "dur_quarter",
    "time_sig",
    "part",
    "articulation",
    "expression",
    "tempo_qpm",
]


def read_csv_rows(path):
    with Path(path).open("r", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        header = list(reader.fieldnames or [])
        rows = list(reader)
    if header[-1:] == [""] and all(row.get("", "") == "" for row in rows):
        header = header[:-1]
        rows = [{key: value for key, value in row.items() if key != ""} for row in rows]
    return header, rows


def raw_f0_path(track):
    return Path(track.path_f0).with_name(
        Path(track.path_f0).name.replace("_f0_filled.csv", "_f0.csv")
    )


def alignment_path(track):
    return (
        Path(track.path_notes).parent.parent
        / "alignments"
        / Path(track.path_notes).name.replace("_notes.csv", ".csv")
    )


def expected_csv_header(path, dataset_root):
    path = Path(path)
    if path.parent == dataset_root and path.name in ROOT_CSV_FIELDS:
        return ROOT_CSV_FIELDS[path.name]
    if path.parent.name == "alignments":
        return ALIGNMENT_FIELDS
    if path.parent.name == "annotations":
        if path.name == "chords.csv":
            return CHORD_FIELDS
        if path.name.endswith("_notes.csv"):
            return NOTES_FIELDS
        if path.name.endswith("_f0_filled.csv"):
            return FILLED_F0_FIELDS
        if path.name.endswith("_f0.csv"):
            return RAW_F0_FIELDS
    if path.parent.parent == dataset_root:
        return SCORE_FIELDS
    raise AssertionError(f"No v1.1 CSV schema registered for {path}")


def note_intervals(notes):
    return [
        (
            Decimal(note["start_sec"]),
            Decimal(note["start_sec"]) + Decimal(note["dur_sec"]),
        )
        for note in notes
    ]


def time_in_intervals(time, intervals):
    tolerance = Decimal("0.001")
    return any(
        start - tolerance <= time <= end + tolerance
        for start, end in intervals
    )


PITCH_NAME_PATTERN = re.compile(r"^([A-G])([#b]*)(-?\d+)$")
PITCH_CLASSES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ACCIDENTALS = {"": 0, "#": 1, "##": 2, "b": -1, "bb": -2}


def pitch_name_to_midi(pitch_name):
    match = PITCH_NAME_PATTERN.fullmatch(pitch_name)
    assert match is not None, f"Unsupported pitch name: {pitch_name}"
    pitch_class, accidental, octave = match.groups()
    return (
        (int(octave) + 1) * 12
        + PITCH_CLASSES[pitch_class]
        + ACCIDENTALS[accidental]
    )


"""
    Test Fixtures
"""
@pytest.fixture(name="choralebricks")
def songdb():
    """ChoraleBricks Dataset"""
    choralebricks = SongDB()
    yield choralebricks


@pytest.fixture
def tracks(choralebricks):
    """All Dataset Tracks"""
    return [track for song in choralebricks.songs for track in song.tracks]


@pytest.fixture
def songs(choralebricks):
    """All Dataset Songs"""
    return choralebricks.songs


@pytest.fixture
def ensembles(choralebricks):
    """All Possible Ensemble Permutations"""
    return [ens for song in choralebricks.songs for ens in EnsemblePermutations(song)]


"""
    Data Integration Tests
"""
def test_number_of_songs(songs):
    """Test number of songs"""
    assert len(songs) == 10


def test_track_count(choralebricks, tracks):
    assert len(tracks) == 193


def test_number_of_ensembles(ensembles):
    """Test number of ensembles"""
    assert len(ensembles) == 4582


def test_paths_audio_not_none(tracks):
    """Test paths for each track"""
    for track in tracks:
        assert track.path_audio is not None


def test_paths_f0_not_none(tracks):
    """Test paths for each track"""
    for track in tracks:
        assert track.path_f0 is not None


def test_paths_notes_not_none(tracks):
    """Test paths for each track"""
    for track in tracks:
        assert track.path_notes is not None


def test_files_exist(tracks):
    """Test files exist"""
    for track in tracks:
        assert Path(track.path_audio).exists()
        assert Path(track.path_f0).exists()
        assert Path(track.path_notes).exists()


def test_files_not_empty(tracks):
    """Test files are not empty"""
    for track in tracks:
        assert Path(track.path_audio).stat().st_size != 0
        assert Path(track.path_f0).stat().st_size != 0
        assert Path(track.path_notes).stat().st_size != 0


def test_track_suffix(tracks):
    """Test track suffix."""
    for track in tracks:
        assert Path(track.path_audio).suffix == ".wav"
        assert Path(track.path_f0).suffix == ".csv"
        assert Path(track.path_notes).suffix == ".csv"


def test_csv_headers(choralebricks):
    """Test every dataset CSV uses semicolons and the v1.1 header."""
    for path in choralebricks.root_dir.rglob("*.csv"):
        header, _ = read_csv_rows(path)
        assert len(header) > 1, f"{path} is not parseable as a semicolon-delimited dataset CSV"
        assert header == expected_csv_header(path, choralebricks.root_dir)


def test_score_rows_are_sorted_by_start_and_satb(songs):
    for song in songs:
        _, rows = read_csv_rows(song.tracks[0].path_sheet_music_csv)
        keys = [
            (Decimal(row["start_meas"]), SCORE_PART_ORDER[row["part"]])
            for row in rows
        ]
        assert keys == sorted(keys)


def test_measure_format_and_exclusive_ends(choralebricks):
    affected_rows = 0
    for path in choralebricks.root_dir.rglob("*.csv"):
        header, rows = read_csv_rows(path)
        if "start_meas" not in header and "end_meas" not in header:
            continue
        assert "start_meas" in header and "end_meas" in header
        for row in rows:
            assert Decimal(row["start_meas"]).quantize(Decimal("0.001")) == Decimal(row["start_meas"])
            assert Decimal(row["end_meas"]).quantize(Decimal("0.001")) == Decimal(row["end_meas"])
            end = Decimal(row["end_meas"])
            assert end != end.to_integral_value()
        affected_rows += len(rows)
    assert affected_rows == 11447


def test_pitch_spellings_match_midi(songs):
    score_rows = 0
    note_rows = 0
    for song in songs:
        _, rows = read_csv_rows(song.tracks[0].path_sheet_music_csv)
        for row in rows:
            assert Decimal(row["pitch_written"]) == pitch_name_to_midi(
                row["pitch_written_name"]
            )
        score_rows += len(rows)
        for track in song.tracks:
            _, notes = read_csv_rows(track.path_notes)
            _, alignment = read_csv_rows(alignment_path(track))
            for note in notes:
                assert int(note["pitch"]) == pitch_name_to_midi(note["pitch_name"])
                assert int(note["pitch_written"]) == pitch_name_to_midi(note["pitch_written_name"])
            for aligned in alignment:
                assert int(aligned["pitch"]) == pitch_name_to_midi(aligned["pitch_name"])
                assert int(aligned["pitch_written"]) == pitch_name_to_midi(aligned["pitch_written_name"])
            note_rows += len(notes)
    assert score_rows == 1887
    assert note_rows == 9097


def test_alignments_match_notes_and_scores(songs):
    note_rows = 0
    for song in songs:
        _, score_rows = read_csv_rows(song.tracks[0].path_sheet_music_csv)
        score_by_part = {
            part: sorted(
                (row for row in score_rows if row["part"] == part),
                key=lambda row: Decimal(row["start_quarter"]),
            )
            for part in ("S", "A", "T", "B")
        }
        for track in song.tracks:
            _, notes = read_csv_rows(track.path_notes)
            _, alignment = read_csv_rows(alignment_path(track))
            assert len(notes) == len(alignment)
            assert [
                {field: row[field] for field in NOTES_FIELDS}
                for row in notes
            ] == [
                {field: row[field] for field in NOTES_FIELDS}
                for row in alignment
            ]
            part = alignment[0]["part"]
            score_voice = score_by_part[part]
            assert len(score_voice) == len(alignment)
            for score_row, alignment_row in zip(score_voice, alignment):
                for field in ALIGNMENT_SCORE_FIELDS:
                    if field in {"start_meas", "end_meas", "start_quarter", "dur_quarter"}:
                        assert Decimal(alignment_row[field]) == Decimal(score_row[field])
                    else:
                        assert alignment_row[field] == score_row[field]
                assert Decimal(alignment_row["pitch_written"]) == Decimal(score_row["pitch_written"])
            note_rows += len(notes)
    assert note_rows == 9097


def test_f0_annotations(tracks):
    note_rows = 0
    for track in tracks:
        _, notes = read_csv_rows(track.path_notes)
        _, raw = read_csv_rows(raw_f0_path(track))
        _, filled = read_csv_rows(track.path_f0)
        intervals = note_intervals(notes)

        raw_times = [Decimal(row["t"]) for row in raw]
        raw_values = [Decimal(row["f0"]) for row in raw]
        assert raw_times == sorted(raw_times)
        assert all(value > 0 for value in raw_values)
        assert all(time_in_intervals(time, intervals) for time in raw_times)

        filled_times = [Decimal(row["t"]) for row in filled]
        assert filled_times == sorted(filled_times)
        assert len(filled_times) == len(set(filled_times))
        filled_steps = [
            later - earlier
            for earlier, later in zip(filled_times, filled_times[1:])
        ]
        assert all(step > 0 for step in filled_steps)
        median_step = sorted(filled_steps)[len(filled_steps) // 2]
        assert max(filled_steps) <= median_step * 2
        for row in filled:
            time = Decimal(row["t"])
            value = Decimal(row["f0"])
            if value == 0:
                assert row["f0"] == "0.0"
            else:
                assert time_in_intervals(time, intervals)

        note_rows += len(notes)
    assert note_rows == 9097


def test_track_samplerate(tracks):
    """Test if all tracks have the same samplerate."""
    for track in tracks:
        if track.path_audio:
            _, sr = sf.read(track.path_audio)
            assert sr == track.sample_rate


def test_track_min_samples(tracks):
    """Test if track has the given min_samples."""
    for track in tracks:
        if track.path_audio:
            data, _ = sf.read(track.path_audio)
            assert len(data) == track.min_samples


def test_track_len_per_song(songs):
    """Test if all songs have tracks with same number of samples."""
    for song in songs:
        track_lengths = []
        for track in song.tracks:
            if track.path_audio:
                data, _ = sf.read(track.path_audio)
                track_lengths.append(len(data))
        assert len(set(track_lengths)) <= 1, f"Not all audio files of {song.id} have the same length."


def test_dur_f0_audio(tracks):
    """Audio and F0-annotations should have similar length (+-1 seconds)"""
    for track in tracks:
        dur_audio = track.min_samples / track.sample_rate
        path_sv_f0 = Path(str(track.path_f0).replace("_filled", ""))
        dur_f0 = read_f0_sv(path_sv_f0).tail(1)["t"].values[0]
        assert np.abs(dur_audio - dur_f0) < 1.0


def test_dur_note_audio(tracks):
    """Audio and note annotations should have similar length (+-1 seconds)"""
    for track in tracks:
        dur_audio = track.min_samples / track.sample_rate
        last_note = read_notes(track.path_notes).tail(1)
        dur_notes = last_note["end_sec"].values[0]
        assert np.abs(dur_audio - dur_notes) < 1.0


def test_chord_annotations_sequence(tracks):
    """Test if CSV chord annotations can be parsed into a ChordSequence"""

    seen_chord_paths = set()
    for track in tracks:
        if track.path_chords in seen_chord_paths:
            continue
        seen_chord_paths.add(track.path_chords)
        cs = ChordSequence.from_csv(track.path_chords)
        # all songs should have a chord in the second measure
        assert cs.get_chord_at(2.25).root is not None, f"Chord for song {track.song_id} not parsed correctly."
        for i in range(len(cs.bounds)-1):
            if cs.bounds[i,1] > cs.bounds[i+1,0]:
                print(track.song_id, i, cs.bounds[i,1], cs.bounds[i+1,0])
        assert np.all(cs.bounds[:-1,1] <= cs.bounds[1:,0]), f"Overlapping chord annotations for song {track.song_id}."
