"""
    For each piece in ChoraleBricks, we pick a random ensemble and write a WAV.
    Furthermore, each track has random gain between -6 and +6 dB.
"""
import logging
from pathlib import Path
import soundfile as sf
import numpy as np

from choralebricks.dataset import SongDB, EnsembleRandom, MixerSimple

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()
    path_mixes = Path("examples/output_random_mixes")
    path_mixes.mkdir(parents=True, exist_ok=True)

    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")
        
        # Draw random ensemble...
        cur_ensemble = EnsembleRandom(cur_song)
        
        # Get the associated tracks...
        cur_tracks = cur_ensemble.get_tracks()
        
        # Draw random gains...
        random_gains = np.random.uniform(-6, 6, size=4)

        # Mix it...
        cur_ensembles_mix = MixerSimple(cur_tracks, gains=random_gains)
        cur_ensembles_mix = cur_ensembles_mix.get_mix()

        # Write output.
        sf.write(
            path_mixes / f"{cur_song.id}.wav",
            data=cur_ensembles_mix["MIX"],
            samplerate=cur_ensembles_mix["SAMPLERATE"]
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
