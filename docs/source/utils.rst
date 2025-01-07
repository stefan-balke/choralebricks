Utils
=====

Collection of helper functions for CSV handling and frequent conversions.


CSV Handling
------------

Each track provides pathes to the annotations.
The following functions provide access to reading parses, including schema validation.

.. autosummary::

    choralebricks.utils.read_f0
    choralebricks.utils.read_notes
    choralebricks.utils.read_sheet_music_csv
    choralebricks.utils.read_chords


Conversions
-----------

.. autosummary::

    choralebricks.utils.voice_to_name
    choralebricks.utils.get_voice_from_int
    choralebricks.utils.midi2hz
    choralebricks.utils.hz2midi

