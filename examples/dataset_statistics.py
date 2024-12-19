import logging
from pathlib import Path
import pandas as pd
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns

from choralebricks.dataset import SongDB, EnsemblePermutations
from choralebricks.constants import (
    Instrument, Voices, VOICE_COLORS, VOICE_STRINGS, VOICE_STRINGS_SHORT
)
from choralebricks.utils import voice_to_name, get_voice_from_int, read_sheet_music_csv
from choralebricks.generators import tracks

logger = logging.getLogger(__name__)


def main():
    cbdb = SongDB()

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
            cur_track_info["player_id"] = cur_track.player_id
            cur_track_info["audio_dur"] = cur_track_wav_info.duration
            cur_track_durs.append(cur_track_wav_info.duration)

            df_tracks.append(cur_track_info)

        cur_song_info["min_dur"] = min(cur_track_durs)
        df_songs.append(cur_song_info)

    df_tracks = pd.DataFrame(df_tracks)
    df_songs = pd.DataFrame(df_songs)

    print(u"\u2500" * 40)
    print(f"#Songs: {df_tracks["song_id"].nunique()}")
    print(f"#Tracks: {df_tracks.shape[0]}")
    print(u"\u2500" * 40)

    print(u"\u2500" * 40)
    print("#Tracks per Song")
    print(u"\u2500" * 40)
    print(df_tracks.groupby("song_id").size())

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
    print(df_tracks.groupby("instrument").agg(
        size=("audio_dur", "size"),
        sum=("audio_dur", "sum"),
        )
    )

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
    dataset_dur = df_songs["perm_dur"].sum()
    df_songs["perm_dur"] = pd.to_datetime(df_songs["perm_dur"], unit='s').dt.strftime('%H:%M:%S')
    print(df_songs.sort_values("song_id"))
    dataset_dur = pd.to_datetime(dataset_dur, unit='s').strftime('%H:%M:%S')
    print(f"Total Duration: {dataset_dur}")

    grouped = df_tracks.groupby(["voice", "instrument"]).size()
    grouped = grouped.reset_index().sort_values(by=["voice", 0], ascending=True)
    grouped = grouped.set_index(["voice", "instrument"])
    
    # Tracks per Instrument and Voice
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
    ax.set_title("Number of Tracks per Voice and Instrument", fontsize=16)
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

    # Plot for Pitch Histograms for SATB
    notes = {
        Voices.SOPRANO: [],
        Voices.ALTO: [],
        Voices.TENOR: [],
        Voices.BASS : []
    }

    # iterate over all available tracks and get the path to the audio file
    for cur_track in list(tracks()):
        cur_sheet_music = read_sheet_music_csv(cur_track.path_sheet_music_csv)

        for cur_part, cur_notes in cur_sheet_music.groupby("part"):
            notes[VOICE_STRINGS_SHORT[cur_part]].extend(cur_notes["pitch"].tolist())

    fig, axes = plt.subplots(4, 1, figsize=(4, 8),sharex=True, sharey=True)
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

        # only for the count
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
        axes_flat[cur_idx].set_xlim((35, 80))
        ax_count.set_ylim((0, 2375))
        ax_count.set_ylabel("#Note Events")
        axes_flat[cur_idx].set_title(VOICE_STRINGS[cur_voice], fontsize=16)
        axes_flat[cur_idx].set_xlabel("MIDI Pitch")
        
    plt.tight_layout()
    plt.savefig('pitch_hist_SATB.pdf')

    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
