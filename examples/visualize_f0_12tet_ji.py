"""Visualize F0, 12-tone equal temperament (12TET) and just intonation (JI) pitch
based on F0, score and chord annotations

Author: Simon Schwär <simon.schwaer@audiolabs-erlangen.de>
Date: Dec 29, 2024
"""
import librosa
import numpy as np
import pandas as pd
from scipy.ndimage import maximum_filter1d

import matplotlib.pyplot as plt

import choralebricks

voice2str = {
    1: "S",
    2: "A",
    3: "T",
    4: "B",
}

# JI offset by scale degree in semitones (using 7-limit tritone)
ji_offset = np.array([0, 11.7, 3.9, 15.6, -13.7, -2, -17.5, 2, 13.7, -15.6, 17.6, -11.7]) / 100

H = 256 # target annotation hop size in samples
fs = 44100. # sampling rate in Hz


def main():
    track = list(choralebricks.generators.tracks())[0]

    ########################
    # 1. load annotations
    ########################

    # load chord annotation as a ChordSequence
    chord_seq = choralebricks.ChordSequence.from_csv(track.path_chords)

    # load score as a Pandas data frame and select only the required voice/part
    score_all = pd.read_csv(track.path_sheet_music_csv, delimiter=";")
    score = score_all[score_all.part == voice2str[track.voice]]

    # load F0 annotations
    f0_a = np.loadtxt(track.path_f0, skiprows=1, usecols=(0, 1), delimiter=",")
    # make sure that f0 annotations are unique for each time frame
    # TODO: can be removed when annotations are correct
    _, idx = np.unique(f0_a[:,0], return_index=True)
    f0_a = f0_a[idx,:]

    # load note annotations
    notes = np.loadtxt(track.path_notes, skiprows=1, usecols=(0, 1, 2), delimiter=",")

    # load audio
    x, _ = librosa.load(track.path_audio, sr=fs)


    ##################################
    # 2. prepare pitch trajectories
    ##################################
    t_f0 = np.arange(0, len(x), H) / fs # target annotation time axis

    # manual linear interpolation of original F0 to target annotation hop size, accounting for unvoiced frames
    # where the distance between the two neighboring interpolation time points is too large, unvoiced frames are inserted
    f0_or = np.zeros_like(t_f0)

    dt = np.diff(f0_a[:,0])
    dt_max_allowed = np.min(dt) * 1.0001 # final factor to accomodate rounding errors up to 1e-4

    # find nearest lower support point for each interpolation target
    idxs = np.searchsorted(f0_a[:,0], t_f0) - 1
    idxs[(idxs >= len(f0_a) - 1)] = len(f0_a) - 2

    # only interpolate points which are close to the lower support point
    t_idx = np.take(f0_a[:,0], idxs)
    t_diff = (t_f0 - t_idx)
    mask = (t_diff >= 0) & (t_diff <= dt_max_allowed)

    # perform linear interpolation for the selected points
    h = t_diff[mask] / np.take(dt, idxs[mask])
    f0_or[mask] = (1 - h) * np.take(f0_a[:,1], idxs[mask]) + h * np.take(f0_a[:,1], idxs[mask] + 1)

    f0_et = np.zeros_like(t_f0)
    f0_ji = np.zeros_like(t_f0)

    i = 0
    for _, row in score.iterrows():
        assert row.pitch == np.round(choralebricks.utils.hz2midi(notes[i,1], f_ref=442)).astype(int)
        chord = chord_seq.get_chord_at(row.start_meas)
        mask = ((t_f0 >= notes[i,0]) & (t_f0 <= (notes[i,0] + notes[i,2])))
        # extend mask a bit for smoother synthesis
        mask = maximum_filter1d(mask, 11, mode='constant', cval=0)

        f0_et[mask] = choralebricks.utils.midi2hz(row.pitch, f_ref=442)
        f0_ji[mask] = choralebricks.utils.midi2hz(row.pitch + ji_offset[chord.get_interval(row.pitch)], f_ref=442)
        i += 1


    #################
    # 3. visualize
    #################
    N = 2048
    X = np.log(1 + np.abs(librosa.stft(x, n_fft=N, hop_length=H, center=False)))
    f = np.arange(X.shape[0]) * fs / N
    t = librosa.times_like(X, sr=fs, hop_length=H, n_fft=N)

    plt.figure(figsize=(16, 9))

    mask = (t <= 10.5)
    plt.pcolormesh(t[mask], f, X[:,mask], cmap="gray_r")

    mask = (t_f0 <= 10.5)
    plt.plot(t_f0[mask], f0_or[mask], "o", ms=3, alpha=0.5, label="F0")
    plt.plot(t_f0[mask], f0_et[mask], "o", ms=3, alpha=0.5, label="12TET")
    plt.plot(t_f0[mask], f0_ji[mask], "o", ms=3, alpha=0.5, label="JI")

    plt.xlim(0, 10.5)
    plt.ylim(200, 600)

    plt.legend()

    plt.show()

if __name__ == "__main__":
    main()
