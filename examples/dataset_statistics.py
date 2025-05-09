"""
    Overview statistics for ChoraleBricks.
    Used for the tables and figures in the corresponding dataset publication.
"""
import logging
from pathlib import Path
import os
import pandas as pd
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib
import seaborn as sns

from choralebricks.dataset import SongDB, EnsemblePermutations
from choralebricks.constants import (
    Instrument, Voices, VOICE_COLORS, VOICE_STRINGS
)
from choralebricks.utils import voice_to_name, get_voice_from_int, read_notes
from choralebricks.generators import tracks

logger = logging.getLogger(__name__)


def collect_data(cbdb):
    df_songs = []
    df_tracks = []

    # collect data for statistics
    for cur_song in cbdb.songs:
        logger.info(f"Processing {cur_song}...")

        cur_song_info = dict()
        cur_song_info["song_id"] = cur_song.id

        # get the permutations
        cur_ensembles = EnsemblePermutations(cur_song)
        cur_song_info["n_permutations"] = len(cur_ensembles)

        cur_track_durs = list()

        for cur_track in cur_song.tracks:
            cur_track_wav_info = sf.info(cur_track.path_audio)

            cur_track_info = dict()
            cur_track_info["song_id"] = cur_track.song_id
            cur_track_info["voice"] = cur_track.voice
            cur_track_info["instrument"] = cur_track.instrument.value
            cur_track_info["instrument_type"] = cur_track.instrument_type.value
            cur_track_info["performer"] = cur_track.performer
            cur_track_info["room"] = cur_track.room
            cur_track_info["microphone"] = cur_track.microphone
            cur_track_info["date"] = cur_track.date
            cur_track_info["audio_dur"] = cur_track_wav_info.duration
            cur_track_durs.append(cur_track_wav_info.duration)

            df_tracks.append(cur_track_info)

        cur_song_info["min_dur"] = min(cur_track_durs)
        df_songs.append(cur_song_info)

    df_songs = pd.DataFrame(df_songs)
    df_tracks = pd.DataFrame(df_tracks)
    df_tracks["date"] = pd.to_datetime(df_tracks["date"], format="%Y-%m-%d")

    return df_songs, df_tracks


def print_tables(df_songs, df_tracks, df_performers):
    print(u"\u2500" * 40)
    print(f"#Performers: {df_performers.shape[0]}")
    print(f"Min. Age: {(2025 - df_performers["birthyear"]).min()}")
    print(f"Max. Age: {(2025 - df_performers["birthyear"]).max()}")
    print(f"Avg. Age: {(2025 - df_performers["birthyear"]).mean()}")
    print(u"\u2500" * 40)

    print(u"\u2500" * 40)
    print(f"#Songs: {df_tracks["song_id"].nunique()}")
    print(f"#Tracks: {df_tracks.shape[0]}")
    print(u"\u2500" * 40)

    print(u"\u2500" * 40)
    print("#Tracks per Song")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("song_id").size())
    print(f"Avg. Tracks per Song: {df_tracks.groupby("song_id").size().mean()}")

    print(u"\u2500" * 40)
    print("#Tracks per Voice")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("voice").size())

    print(u"\u2500" * 40)
    print("#Tracks per Instrument Type")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("instrument_type").agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
        )
    )

    print(u"\u2500" * 40)
    print("#Tracks per Instrument")
    print(u"\u2500" * 40)
    df_songs_grouped = df_tracks.groupby("instrument").agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
    )
    df_songs_grouped["sum"] = pd.to_datetime(df_songs_grouped["sum"], unit='s').dt.strftime('%H:%M:%S')
    print(f"Avg. Tracks per Instrument: {df_songs_grouped["size"].mean()}")

    audio_dur = df_tracks["audio_dur"].sum()
    total_seconds = int(audio_dur)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"Total Audio Duration: {hours}h {minutes}m {seconds}s")


    print(df_songs_grouped)

    print(u"\u2500" * 40)
    print("#Tracks per Voice and Instrument")
    print(u"\u2500" * 40)
    print(df_tracks.groupby(["voice", "instrument"]).agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
        )
    )

    print(u"\u2500" * 40)
    print("#Ensembles per Song")
    print(u"\u2500" * 40)
    df_songs["perm_dur"] = df_songs["n_permutations"] * df_songs["min_dur"]
    df_songs["perm_dur_str"] = pd.to_datetime(df_songs["perm_dur"], unit='s').dt.strftime('%H:%M:%S')
    print(df_songs.sort_values("song_id"))

    perm_dur = df_songs["perm_dur"].sum()
    total_seconds = int(perm_dur)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"Total Permutation Duration: {hours}h {minutes}m {seconds}s")

    print(f"#Ensembles: {df_songs["n_permutations"].sum()}")
    print(f"Avg. Ensembles: {df_songs["n_permutations"].mean()}")


def figure_tracks_per_voice_instrument(df_tracks):
    # Figure: Tracks per Instrument and Voice
    grouped = df_tracks.groupby(["voice", "instrument"]).size()
    grouped = grouped.reset_index().sort_values(by=["voice", 0], ascending=True)
    grouped = grouped.set_index(["voice", "instrument"])

    fig, ax = plt.subplots(figsize=(10, 8))

    y_tick_labels = []
    legend_entries = []
    for cur_i, (cur_idx, cur_box) in enumerate(grouped.iterrows()):
        cur_voice = get_voice_from_int(cur_idx[0])
        cur_instrument = Instrument(cur_idx[1])
        cur_color = VOICE_COLORS[cur_voice]

        ax.add_patch(
            plt.Rectangle(
                (0, cur_i - 0.5),
                cur_box.values[0],
                1,
                color=cur_color,
                alpha=0.3
            )
        )

        y_tick_labels.append(f"{cur_instrument.value}")

    for cur_voice in Voices:
        legend_entries.append(
            Patch(
                facecolor=VOICE_COLORS[cur_voice],
                edgecolor=VOICE_COLORS[cur_voice],
                alpha=0.3,
                label=voice_to_name(cur_voice.value)
            )
        )

    # Customize the legend and axes
    fig.legend(handles=legend_entries, loc="upper right", fontsize=12)
    # ax.set_title("Number of Tracks per Voice and Instrument", fontsize=16)
    ax.set_xlabel("#Tracks", fontsize=14)
    ax.set_ylabel("Instrument", fontsize=14)
    ax.set_xlim(0, 11)
    ax.spines['top'].set_visible(False)  # Remove the top spine
    ax.spines['right'].set_visible(False)  # Remove the right spine
    ax.set_ylim(-1, grouped.shape[0])
    ax.set_yticks(np.arange(len(y_tick_labels)))
    ax.set_yticklabels(y_tick_labels)
    ax.invert_yaxis()
    plt.tight_layout()

    plt.savefig('tracks_per_voice_instrument.pdf')


def figure_pitch_hist_SATB():
    # Figure: Pitch Histograms for SATB
    notes = {
        Voices.SOPRANO: [],
        Voices.ALTO: [],
        Voices.TENOR: [],
        Voices.BASS : []
    }

    # collect all played notes from the whole collection
    for cur_track in list(tracks()):
        try:
            cur_notes = read_notes(cur_track.path_notes)

            notes[Voices(cur_track.voice)].extend(cur_notes["pitch"].tolist())
        except FileNotFoundError:
            print(f"Skipping notes from {cur_track.song_id}_{cur_track.voice}_{cur_track.instrument}. Reason: No annotations.")

    fig, axes = plt.subplots(2, 2, figsize=(10, 6),sharex=True, sharey=True)
    axes_flat = axes.ravel()

    for cur_idx, cur_voice in enumerate(Voices):
        cur_df = pd.DataFrame(notes[cur_voice], columns=["midi_pitch"])

        sns.histplot(
            cur_df['midi_pitch'],
            bins=20,
            stat="density",
            kde=True,
            color="k",
            alpha=0.1,
            lw=0.1,
            ax=axes_flat[cur_idx]
        )

        # add for the count
        ax_count = axes_flat[cur_idx].twinx()
        sns.histplot(
            cur_df['midi_pitch'],
            bins=20,
            stat="frequency",
            color="r",
            alpha=0,
            lw=0,
            ax=ax_count
        )

        sns.kdeplot(
            cur_df['midi_pitch'],
            fill=True,
            color=VOICE_COLORS[cur_voice],
            alpha=0.6,
            ax=axes_flat[cur_idx]
        )

        sns.despine(right=False)
        axes_flat[cur_idx].set_xlim((20, 90))
        ax_count.set_ylim((0, 2375))
        ax_count.set_ylabel("#Note Events")
        axes_flat[cur_idx].set_title((
                f"{VOICE_STRINGS[cur_voice]}: "
                f"[{cur_df['midi_pitch'].min():.0f}:{cur_df['midi_pitch'].max():.0f}], "
                f"\u00D8={cur_df['midi_pitch'].mean():.2f}"
                # f"mode={cur_df['midi_pitch'].mode().values[0]:.0f}"
            ),
            fontsize=12)
        axes_flat[cur_idx].set_xlabel("MIDI Pitch")

    plt.tight_layout()
    plt.savefig('pitch_hist_SATB.pdf')


def figure_timeline_recordings(df_tracks):
    # Figure: Timeline of Number of Records per Day
    df_timeline = df_tracks[["date", "instrument"]]
    df_timeline.set_index("date", inplace=True)
    daily_counts = df_timeline.groupby([pd.Grouper(freq="D"), "instrument"]).size().unstack(fill_value=0)

    # Choose a colormap
    cmap = matplotlib.colormaps.get_cmap('tab20')

    # Generate colors
    colors = [cmap(i) for i in range(len(daily_counts.columns))]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))

    bottom = None
    for idx, instrument in enumerate(daily_counts.columns):
        ax.bar(
            daily_counts.index,
            daily_counts[instrument],
            bottom=bottom,
            label=instrument,
            color=colors[idx],
            width=1.0,
            align='center'
        )
        if bottom is None:
            bottom = daily_counts[instrument]
        else:
            bottom = bottom + daily_counts[instrument]

    # Decorations
    ax.set_title("Timeline of Number of Records per Day (by Instrument)", fontsize=16)
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Number of Records", fontsize=14)
    ax.legend(title="Instrument", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig('timeline_recordings_stacked.pdf')


def main():
    cbdb = SongDB()
    df_songs, df_tracks = collect_data(cbdb)
    df_performers = pd.read_csv(Path(os.environ["CHORALEDB_PATH"]) / "metadata_performers.csv", sep=";")

    print_tables(df_songs=df_songs, df_tracks=df_tracks, df_performers=df_performers)
    figure_tracks_per_voice_instrument(df_tracks)
    figure_pitch_hist_SATB()
    figure_timeline_recordings(df_tracks)

    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
