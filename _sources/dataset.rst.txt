Dataset
=======

Dataset Classes
---------------

Hierarchical model of the dataset and direct access to the data.
All metadata, e.g., piece name, are available as class properties.
The actual audio data and the annotations are provided as pathes.

.. autosummary::
    choralebricks.dataset.Track
    choralebricks.dataset.Song
    choralebricks.dataset.SongDB

Ensemble Classes
----------------

In ChoraleBricks, an ensemble consists of four voices (soprano, tenor, alt, and bass).
The task of the `Ensemble` classes is to select the respective tracks from a `choralebricks.Song` in different ways:

.. autosummary::
    choralebricks.dataset.EnsemblePermutations
    choralebricks.dataset.EnsembleRandom

Mixer Classes
-------------

Given an `choralebricks.Ensemble`, the `Mixer` classes provie a way of summing the audio recordings in various ways,
e.g., simple sum or more advanced mixing such as equal loudness.

.. autosummary::
    choralebricks.dataset.MixerSimple
