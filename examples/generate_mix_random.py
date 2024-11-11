import logging
from pathlib import Path
import soundfile as sf

from choralebricks.dataset import SongDB, EnsembleRandom, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()

    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")
        cur_ensemble = EnsembleRandom(cur_song)
        cur_tracks = cur_ensemble.get_tracks()
        cur_ensembles_mix = MixerSimple(cur_tracks).get_mix()
        sf.write(
            Path("examples") / f"{cur_song.id}.wav",
            data=cur_ensembles_mix["MIX"],
            samplerate=cur_ensembles_mix["SAMPLERATE"]
        )
        print(cur_ensembles_mix)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
