from enum import Enum
import matplotlib.pyplot as plt


NUM_VOICES = 4

class Voices(Enum):
    """
    Available voices (SATB).
    """
    SOPRANO = 1
    ALTO = 2
    TENOR = 3
    BASS = 4

class Instrument(Enum):
    """
    Insturments and their abbreviations.
    """
    FLUTE = "fl"
    OBOE = "ob"
    ENGLISH_HORN = "eh"
    CLARINET = "cl"
    CLARINET_BASS = "bcl"
    SAX_ALTO = "as"
    SAX_TENOR = "ts"
    SAX_BARITONE = "bs"
    TRUMPET = "tp"
    FLUGELHORN = "fh"
    BARITONE = "bar"
    FRENCHHORN = "fho"
    TROMBONE = "tb"
    TUBA = "tba"


INSTRUMENT_STRINGS = {
    # Dictionary from `Instrument` to `str`.
    Instrument.TRUMPET: "Trumpet",
    Instrument.FLUGELHORN: "Flugelhorn",
    Instrument.BARITONE: "Baritone",
    Instrument.FRENCHHORN: "French horn",
    Instrument.TROMBONE: "Trombone",
    Instrument.TUBA: "Tuba",
    Instrument.FLUTE: "Flute",
    Instrument.OBOE: "Oboe",
    Instrument.ENGLISH_HORN: "English horn",
    Instrument.CLARINET: "Clarinet",
    Instrument.CLARINET_BASS: "Bass Clarinet",
    Instrument.SAX_ALTO: "Alto Saxophone",
    Instrument.SAX_TENOR: "Tenor Saxophone",
    Instrument.SAX_BARITONE: "Baritone Saxophone"
}


class InstrumentType(Enum):
    """
    Instrument families.
    """
    BRASS = "brass"
    WOODWIND = "woodwind"


INSTRUMENTS_BRASS = [
    # List of brass instruments.
    Instrument.TRUMPET,
    Instrument.FLUGELHORN,
    Instrument.BARITONE,
    Instrument.FRENCHHORN,
    Instrument.TROMBONE,
    Instrument.TUBA
]


INSTRUMENTS_WOODWIND = [
    # List of woodwind instruments.
    Instrument.FLUTE,
    Instrument.OBOE,
    Instrument.ENGLISH_HORN,
    Instrument.CLARINET,
    Instrument.CLARINET_BASS,
    Instrument.SAX_ALTO,
    Instrument.SAX_TENOR,
    Instrument.SAX_BARITONE
]

VOICE_COLORS = {
    # Mapping from Voices to plot colors.
    Voices.SOPRANO: plt.cm.tab10(3),
    Voices.ALTO: plt.cm.tab10(2),
    Voices.TENOR: plt.cm.tab10(1),
    Voices.BASS: plt.cm.tab10(0)
}

VOICE_STRINGS = {
    # Dictionary from `Voice` to `str`.
    Voices.SOPRANO: "S",
    Voices.ALTO: "A",
    Voices.TENOR: "T",
    Voices.BASS: "B"
}

VOICE_STRINGS_SHORT = {
    # Dictionary from `str` to `Voice`.
    "S": Voices.SOPRANO,
    "A": Voices.ALTO,
    "T": Voices.TENOR,
    "B": Voices.BASS
}
