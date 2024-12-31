from enum import Enum
import matplotlib.pyplot as plt


NUM_VOICES = 4

class Voices(Enum):
    SOPRANO = 1
    ALTO = 2
    TENOR = 3
    BASS = 4

class Instrument(Enum):
    FLUTE = "fl"
    OBOE = "ob"
    ENGLISH_HORN = "eh"
    CLARINET = "cl"
    CLARINET_BASS = "bcl"
    SAX_ALTO = "as"
    SAX_TENOR = "ts"
    SAX_BARITONE = "bs"
    TRUMPET = "tp"
    FLUEGELHORN = "fh"
    BARITONE = "bar"
    FRENCHHORN = "fho"
    TROMBONE = "tb"
    TUBA = "tba"


class InstrumentType(Enum):
    BRASS = "brass"
    WOODWIND = "woodwind"


INSTRUMENTS_BRASS = [
    Instrument.TRUMPET,
    Instrument.FLUEGELHORN,
    Instrument.BARITONE,
    Instrument.FRENCHHORN,
    Instrument.TROMBONE,
    Instrument.TUBA
]


INSTRUMENTS_WOODWIND = [
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
    Voices.SOPRANO: plt.cm.tab10(3),
    Voices.ALTO: plt.cm.tab10(2),
    Voices.TENOR: plt.cm.tab10(1),
    Voices.BASS: plt.cm.tab10(0)
}

VOICE_STRINGS = {
    Voices.SOPRANO: "S",
    Voices.ALTO: "A",
    Voices.TENOR: "T",
    Voices.BASS: "B"
}

VOICE_STRINGS_SHORT = {
    "S": Voices.SOPRANO,
    "A": Voices.ALTO,
    "T": Voices.TENOR,
    "B": Voices.BASS
}
