import logging
from pathlib import Path
import soundfile as sf

from choralebricks.dataset import SongDB, EnsemblePermutations, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()

    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")
        cur_ensemble_permutations = EnsemblePermutations(cur_song)

        for cur_ensemble in cur_ensemble_permutations:
            # do whatever you need to do with the tracks...
            pass

        # you can now save the mixes as in `generate_mix_random.py`
        # we do not do this here to not flood your hard drive

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
