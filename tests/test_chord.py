"""Test parsing chords in Harte notation
"""
import pytest

import numpy as np
import shutil
from pathlib import Path

from choralebricks import Chord, ChordSequence

def test_chords():
    # test the chord parser
    midi = np.arange(62, 74, 1)

    c = Chord("D:maj")
    assert c.is_nc() == False
    assert c.get_interval(66) == 4
    assert c.get_interval_to_bass(66) == 4
    assert c.is_chord_note(66) == True

    assert np.array_equal(c.get_interval(midi), np.arange(12))
    assert np.array_equal(c.is_chord_note(midi),
                          np.array([True, False, False, False, True, False, False, True, False, False, False, False]))

    c = Chord("F#:(*1,3,5,b7)/5")
    assert c.is_nc() == False
    assert c.get_interval(66) == 0
    assert c.get_interval_to_bass(66) == 5
    assert c.is_chord_note(66) == False

    assert np.array_equal(c.get_interval_to_bass(midi), np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]))

    c = Chord("X")
    assert c.is_nc() == True


def test_chord_sequence_from_csv_reads_semicolon():
    tmp_dir = Path(".tmp") / "test_chords_semicolon"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "chords.csv"
    path.write_text(
        "start_meas;end_meas;chord\n"
        "0.000;1.000;C:maj\n"
        "1.000;2.000;G:maj\n",
        encoding="utf-8",
    )

    try:
        sequence = ChordSequence.from_csv(path)
        assert sequence.get_chord_at(0.5).root_str == "C"
        assert sequence.get_chord_at(1.5).root_str == "G"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_chord_sequence_from_csv_rejects_comma_delimited():
    """Only semicolon-delimited CSVs are accepted (no delimiter fallback)."""
    from choralebricks.utils import SchemaValidationError

    tmp_dir = Path(".tmp") / "test_chords_comma"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "chords.csv"
    path.write_text(
        "start_meas,end_meas,chord\n"
        "0.000,1.000,C:maj\n",
        encoding="utf-8",
    )

    try:
        with pytest.raises(SchemaValidationError):
            ChordSequence.from_csv(path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_chord_sequence_from_csv_rejects_bad_schema():
    from choralebricks.utils import SchemaValidationError

    tmp_dir = Path(".tmp") / "test_chords_bad_schema"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "chords.csv"
    path.write_text(
        "start;ende;label\n"
        "0.000;1.000;C:maj\n",
        encoding="utf-8",
    )

    try:
        with pytest.raises(SchemaValidationError):
            ChordSequence.from_csv(path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
