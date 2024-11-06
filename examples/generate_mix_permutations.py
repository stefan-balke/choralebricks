import logging
from pathlib import Path
import soundfile as sf

from choralebricks.dataset import SongDB, TrackSelectorPermutations, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB(root_dir="/Users/stefan/dev/wind_music_db/data/02_multitrack")

    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")
        cur_song_permutations = TrackSelectorPermutations(cur_song)

        for cur_song_permutation in cur_song_permutations:
            print(cur_song_permutation)

        # you can now save the mixes as in `generate_mix_random.py`
        # we do not do this here to not flood your hard drive

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
