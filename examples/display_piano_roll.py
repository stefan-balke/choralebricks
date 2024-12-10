import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from choralebricks.generators import tracks
from choralebricks.utils import read_notes, read_sheet_music_csv


def main():
    cur_track = list(tracks())[0]

    print(
        cur_track.path_audio.name,
        cur_track.voice,
        cur_track.instrument,
        cur_track.instrument_type
    )

    cur_sheet_music = read_sheet_music_csv(cur_track.path_sheet_music_csv)
    cur_notes = read_notes(cur_track.path_notes)

    ##############################################
    # Plot for piano roll
    ##############################################
 
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    # piano-roll data
    for _, row in cur_sheet_music.iterrows():
        if row["part"] == "S":
            color = "red"
        if row["part"] == "A":
            color = "green"
        if row["part"] == "T":
            color = "orange"
        if row["part"] == "B":
            color = "magenta"

        ax.add_patch(
            plt.Rectangle(
                (row["start_meas"], row["pitch"] - 0.5),
                row["dur_meas"],
                1,
                color=color,
                alpha=0.3
            )
        )

    rectangle_legend = [
        Patch(facecolor="red", edgecolor="red", alpha=0.3, label="S"),
        Patch(facecolor="green", edgecolor="green", alpha=0.3, label="A"),
        Patch(facecolor="orange", edgecolor="orange", alpha=0.3, label="T"),
        Patch(facecolor="magenta", edgecolor="magenta", alpha=0.3, label="B")
    ]
    plt.legend(handles=rectangle_legend, loc="upper right")

    # Labels and legend
    plt.xlabel("Time (measures)")
    plt.ylabel("MIDI Pitch")
    plt.title("Piano-roll Representation")
    plt.grid(alpha=0.3)

    last_note = cur_notes.tail(1)
    plt.xlim((0, cur_sheet_music["end_meas"].max()))
    plt.ylim((20, 100))

    ##############################################
    # Plot for note event annotations
    ##############################################
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    if cur_track.voice == 1:
        color = "red"
    if cur_track.voice == 2:
        color = "green"
    if cur_track.voice == 3:
        color = "orange"
    if cur_track.voice == 4:
        color = "magenta"

    # Note Annotations
    for _, row in cur_notes.iterrows():
        ax.add_patch(
            plt.Rectangle(
                (row["t_start"], row["f0_mean"] - 5),
                row["t_dur"],
                10,
                color=color,
                alpha=0.5
            )
        )

    rectangle_legend = Patch(facecolor=color, edgecolor=color, alpha=0.3, label="Note Events")
    plt.legend(handles=[rectangle_legend], loc="upper right")

    # Labels and legend
    plt.xlabel("Time (sec.)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Note Events from the Annotations")
    plt.grid(alpha=0.3)

    last_note = cur_notes.tail(1)
    plt.xlim((0, 2 + last_note["t_start"].values[0] + last_note["t_dur"].values[0]))
    plt.ylim((0, 600))

    plt.show()


if __name__ == "__main__":
    main()
