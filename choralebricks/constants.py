from enum import Enum


NUM_VOICES = 4

class Instrument(Enum):
    FLUTE = "fl"
    OBOE = "ob"
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
    Instrument.CLARINET,
    Instrument.CLARINET_BASS,
    Instrument.SAX_ALTO,
    Instrument.SAX_TENOR,
    Instrument.SAX_BARITONE
]