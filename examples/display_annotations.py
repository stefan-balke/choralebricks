import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from choralebricks.generators import tracks
from choralebricks.utils import midi2hz, read_f0, read_notes


def main():
    cur_track = list(tracks())[3]

    print(
        cur_track.path_audio.name,
        cur_track.part,
        cur_track.instrument,
        cur_track.instrument_type
    )

    cur_f0 = read_f0(cur_track.path_f0)
    cur_notes = read_notes(cur_track.path_notes)

    mask = cur_f0["t"].apply(
        lambda t: any((t >= row["start_sec"]) and (t <= row["end_sec"]) for _, row in cur_notes.iterrows())
    )

    # Filter cur_f0 using the the notes as mask
    cur_f0_filtered = cur_f0[mask]

    # Plot
    plt.figure(figsize=(12, 5))

    # Base data (first dataframe)
    sc1 = plt.scatter(
        cur_f0["t"],
        cur_f0["f0"],
        label="F0-Trajectory",
        color="blue",
        s=5,
        alpha=0.7
    )

    # Base data (first dataframe)
    sc2 = plt.scatter(
        cur_f0_filtered["t"],
        cur_f0_filtered["f0"],
        label="F0-Trajectory (filt.)",
        color="r",
        s=60,
        alpha=0.8,
        marker="x"
    )

    # Overlay data (second dataframe)
    for _, row in cur_notes.iterrows():
        note_hz = midi2hz(row["pitch"] + row["pitch_dev_cents"] / 100.0, f_ref=440.0)
        plt.gca().add_patch(plt.Rectangle(
            (row["start_sec"], note_hz - 5),
            row["dur_sec"],
            10,
            color="orange",
            alpha=0.3
        ))

    rectangle_legend = Patch(facecolor="orange", edgecolor="orange", alpha=0.3, label="Note Events")
    plt.legend(handles=[sc1, sc2, rectangle_legend], loc="upper right")

    # Labels and legend
    plt.xlabel("Time (sec.)")
    plt.ylabel("Frequency (Hz)")
    plt.title("F0-Trajectory and Note Events from the Annotations")
    plt.grid(alpha=0.3)

    plt.show()


if __name__ == "__main__":
    main()
