"""Representation and parser for chords in the notation format introduced by Harte et al.

Author: Simon Schwär <simon.schwaer@audiolabs-erlangen.de>
Date: Dec 19, 2024

Reference
---------
Harte, Christopher, Mark B. Sandler, Samer A. Abdallah, and Emilia Gómez.
"Symbolic Representation of Musical Chords: A Proposed Syntax for Text Annotations."
In ISMIR, vol. 5, pp. 66-71. 2005.
"""
import math
import os

import numpy as np
import pandas as pd

from lark import Lark, Transformer

class Chord():
    """Representation of a chord provided in Harte notation
    """

    def __init__(self, harte_str):
        """Representation of a chord provided in Harte notation

        Arguments
        ---------
        harte_str : str
            String in Harte format to be parsed
        """
        # defaults (just to be verbose, will be overwritten by the parsed properties)
        self.root = None
        self.root_str = "N.C."
        self.relative_steps = []
        self.bass = 0
        self.harte = harte_str

        cd = HarteChord.parse(self.harte)

        # add parsed properties to the chord object
        for key, val in cd.items():
            assert key in ["root", "root_str", "relative_steps", "bass"], \
                "Unknown property parsed from Harte notation."
            setattr(self, key, val)

    def get_interval(self, midi):
        """Get the interval (0-11) of a given MIDI pitch relative to the root
        """
        return (midi - self.root) % 12

    def get_interval_to_bass(self, midi):
        """Get the interval (0-11) of a given MIDI pitch relative to the bass note
        """
        return (midi - self.root - self.bass) % 12

    def is_chord_note(self, midi):
        """Return whether or not a given MIDI pitch is a member note of the chord
        """
        return np.isin(self.get_interval(np.round(midi).astype(int)), self.relative_steps)

    def is_nc(self):
        """ Return whether or not this is a no chord "N.C."
        """
        return self.root is None


class ChordSequence():

    @staticmethod
    def from_csv(file_path):
        """Read a CSV file with chord annotations into a ChordSequence object

        Expected CSV format: start_meas,end_meas,chord
        where start_meas is the start time of the chord in measures,
              end_meas is the end time of the chord in measures,
              chord is a string label in the notation by Harte et al.

        Arguments
        ---------
        file_path : str or Path
            file path to the CSV file with annotations

        Returns
        -------
        seq : ChordSequence
        """
        df = pd.read_csv(file_path)

        start_meas = df["start_meas"].to_numpy()
        end_meas = df["end_meas"].to_numpy()
        chords = [Chord(s) for s in df["chord"]]

        return ChordSequence(start_meas, end_meas, chords)

    def __init__(self, starts, ends, chords):
        """Initialize a ChordSequence
        """
        assert len(starts.shape) == 1 \
           and np.array_equal(starts.shape, ends.shape) \
           and len(chords) == len(starts), \
           "Inputs to ChordSequence have to be one-dimensional arrays of the same length."

        self.bounds = np.hstack([starts[:,None], ends[:,None]])
        self.chords = chords

    def get_chord_at(self, measure_pos):
        """Get the current chord for a given measure position.

        Returns N.C. if no chord is annotated for this measure position.
        """
        idx = np.where((measure_pos >= self.bounds[:,0]) & (measure_pos < self.bounds[:,1]))

        if len(idx[0]) == 0:
            # return N.C., since no annotation was found
            return Chord("X")

        assert len(idx[0]) == 1, "ChordSequence has overlapping chord annotations."

        return self.chords[idx[0][0]]



class ChordTransformer(Transformer):
    """lark.Transformer instance implementing a visitor pattern on the Lark-parsed chord string

    Only used internally

    Based on an implementation by Andrea Poltronieri
    https://github.com/andreamust/harte-library
    """
    @staticmethod
    def degree_to_step(deg: str):
        """Convert a degree string to a step float (-11.0 to 11.0)

        A negative number indicates that the step should be removed from the final list.
        The step is float to allow for -0.0 (removing the root note)
        """
        str2step = {
            '1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11,
            '8': 12, '9': 2, '10': 4, '11': 5, '12': 7, '13': 9,
        }

        negate = False
        step = 0.
        for i in range(len(deg)):
            if deg[i].isnumeric():
                step += int(str2step[deg[i]])
            elif (deg[i] == '#'):
                step += 1
            elif (deg[i] == 'b'):
                step -= 1
            elif (deg[i] == '*'):
                negate = True

        step = step % 12

        if negate:
            step *= -1 # also making use of negative 0 here!

        return step


    @staticmethod
    def shorthand(shorthand):
        """Convert a shorthand into a step list
        """
        shorthand2steps = {
            "maj":     [0, 4, 7],
            "min":     [0, 3, 7],
            "dim":     [0, 3, 6],
            "aug":     [0, 4, 8],
            "maj7":    [0, 4, 7, 11],
            "min7":    [0, 3, 7, 10],
            "dim7":    [0, 3, 6, 9],
            "hdim7":   [0, 3, 6, 10],
            "minmaj7": [0, 3, 7, 11],
            "maj6":    [0, 4, 7, 9],
            "min6":    [0, 3, 7, 9],
            "maj9":    [0, 4, 7, 11, 2],
            "min9":    [0, 3, 7, 10, 2],
            "sus4":    [0, 5, 7],
            "sus2":    [0, 2, 7],
            "7":       [0, 4, 7, 10],
            "9":       [0, 4, 7, 10, 2],
            "11":      [0, 4, 7, 10, 2, 5],
            "13":      [0, 4, 7, 10, 2, 5, 9],
        }
        return {"steps": shorthand2steps[shorthand[0]]}

    @staticmethod
    def degree(degree):
        """Convert a degree string (e.g. "b3") to a step (e.g. 4.0)
        """
        return ChordTransformer.degree_to_step(''.join(degree))

    @staticmethod
    def bass(bass):
        """Add the bass note to the dict
        """
        return {'bass': int(bass[0])}

    @staticmethod
    def NA(token):
        # "no chord" symbol found
        return {"root": None, "root_str": "N.C."}

    @staticmethod
    def note(root):
        """Add the root note to the dict (absolute step, i.e. 0 == C)
        """
        note_string = "".join(root)

        steps = ['C', '_', 'D', '_', 'E', 'F', '_', 'G', '_', 'A', '_', 'B'].index(note_string[0].upper())
        for i in range(1, len(note_string)):
            if (note_string[i] == '#'):
                steps += 1
            elif (note_string[i] == 'b'):
                steps -= 1
        return {"root": steps, "root_str": note_string}

    @staticmethod
    def degree_list(degrees):
        """Split positive and negative floats into two integer lists
        """
        extra = [int(x) for x in degrees if math.copysign(1, x) == 1]
        remove = [int(x) for x in degrees if math.copysign(1, x) == -1]

        return {"extra": extra, "remove": remove}

    @staticmethod
    def chord(elements):
        """Assemble a final dict
        """
        cd = {"root": None, "root_str": None, "relative_steps": [], "bass": 0}
        for el in elements:
            if isinstance(el, dict):
                if "bass" in el.keys():
                    cd["bass"] = el["bass"]
                if "root" in el.keys():
                    cd["root"] = el["root"]
                if "root_str" in el.keys():
                    cd["root_str"] = el["root_str"]
                if "steps" in el.keys():
                    cd["relative_steps"] += el["steps"]
                if "extra" in el.keys():
                    cd["relative_steps"] += el["extra"]
                if "remove" in el.keys():
                    cd["relative_steps"] = [x for x in cd["relative_steps"] if x not in el["remove"]]

        return cd


_GRAMMAR_FILE = os.path.join(os.path.dirname(__file__), 'harte.lark')

with open(_GRAMMAR_FILE, 'r', encoding='utf-8') as g:
    _HARTE_LARK_GRAMMAR = g.read()

HarteChord = Lark(_HARTE_LARK_GRAMMAR, parser="lalr", start="chord",
                  propagate_positions=False, maybe_placeholders=False, transformer=ChordTransformer())
