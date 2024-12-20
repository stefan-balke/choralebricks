"""Test parsing chords in Harte notation
"""
import pytest

import numpy as np

from choralebricks import Chord

def test_chords():
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