import logging
from pathlib import Path
import soundfile as sf

from choralebricks.dataset import SongDB, TrackSelectorRandom, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB(root_dir="/Users/stefan/dev/wind_music_db/data/02_multitrack")

    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")
        cur_song_filtered = TrackSelectorRandom(cur_song).song
        cur_song_mixed = MixerSimple(cur_song_filtered).get_mix()
        sf.write("test.wav", data=cur_song_mixed["MIX"], samplerate=cur_song_mixed["SAMPLERATE"])
        print(cur_song_mixed)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
