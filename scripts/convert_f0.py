import numpy as np
import pandas as pd
from pathlib import Path
import logging
import soundfile as sf
import matplotlib.pyplot as plt

from choralebricks.generators import tracks
from choralebricks.utils import read_f0_sv, read_sheet_music_csv, voice_to_name


logging.basicConfig(
    filename="scripts/convert_f0.log",  # Log file name
    level=logging.DEBUG,  # Log all levels to the file
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="w",  # Clear the log file at the start
)

def main():
    out_folder = Path("scripts/f0_conversion")
    out_folder.mkdir(parents=True, exist_ok=True)
    cur_track = list(tracks())[0]

    # target hop size for the new F0 annotation
    # this comes from the pYIN plugin in Sonic Visualiser
    H = 256

    # iterate over all available tracks and get the path to the audio file
    for cur_track in list(tracks()):
        logging.info(f"Processing {cur_track}")

        # read audio file
        x, fs = sf.read(cur_track.path_audio)

        # read f0 annotation
        cur_f0_old = read_f0_sv(cur_track.path_f0)
        f0_orig = cur_f0_old.to_numpy()

        # remove duplicates in the original F0 annotation
        _, idx = np.unique(f0_orig[:, 0], return_index=True)
        f0_orig = f0_orig[idx, :]

        # target annotation time axis
        t_f0_new = np.arange(0, len(x), H) / fs

        # manual linear interpolation of original F0 to target annotation hop size, accounting for unvoiced frames
        # where the distance between the two neighboring interpolation time points is too large, unvoiced frames are inserted
        f0_new = np.zeros_like(t_f0_new)

        dt = np.diff(f0_orig[:,0])
        dt_max_allowed = np.min(dt) * 1.0001 # final factor to accomodate rounding errors up to 1e-4

        # find nearest lower support point for each interpolation target
        idxs = np.searchsorted(f0_orig[:,0], t_f0_new) - 1
        idxs[(idxs >= len(f0_orig) - 1)] = len(f0_orig) - 2

        # only interpolate points which are close to the lower support point
        t_idx = np.take(f0_orig[:,0], idxs)
        t_diff = (t_f0_new - t_idx)
        mask = (t_diff >= 0) & (t_diff <= dt_max_allowed)

        # perform linear interpolation for the selected points
        h = t_diff[mask] / np.take(dt, idxs[mask])
        f0_new[mask] = (1 - h) * np.take(f0_orig[:,1], idxs[mask]) + h * np.take(f0_orig[:,1], idxs[mask] + 1)

        # create new pandas dataframe for the new F0 annotation
        cur_f0_new = pd.DataFrame()
        cur_f0_new["t"] = t_f0_new
        cur_f0_new["f0"] = f0_new
        cur_f0_new.to_csv(cur_track.path_f0.with_name(cur_track.path_f0.stem + "_filled.csv"), index=False)

        print(cur_f0_old.shape, cur_f0_new.shape)

        # plot the original and the new F0 annotation for debugging
        plt.figure()
        plt.plot(cur_f0_old["t"], cur_f0_old["f0"], label="original")
        plt.plot(t_f0_new, f0_new, label="new")
        plt.legend()
        plt.xlabel("Time [s]")
        plt.ylabel("Frequency [Hz]")
        plt.title(f"F0 annotation for {cur_track.song_id}")
        plt.savefig(out_folder / f"{cur_track.song_id}_f0_{cur_track.instrument}.png")
        plt.close()

if __name__ == "__main__":
    main()
