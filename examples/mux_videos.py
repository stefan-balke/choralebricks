""" With this script, you can create similar mixes as we use on the accompanying website.
Furthermore, the mixes are combined with the conducting videos.

Note: This script needs a local installation of ffmepg.

Author: Stefan Balke
Date: Apr 1st, 2025
"""

from pathlib import Path
import os
import pandas as pd
import numpy as np
import soundfile as sf
import subprocess
from choralebricks.dataset import SongDB, MixerSimple
from choralebricks.constants import Instrument

###################
# You need to adjust these paths!
###################
PATH_DATASET = Path(os.environ["CHORALEDB_PATH"])
PATH_DATASET_ROOT = PATH_DATASET.parent
PATH_VIDEOS = PATH_DATASET_ROOT / "02_ConductingVideos"
PATH_VIDEO_OFFSETS = PATH_DATASET / "metadata_video_offsets.csv"
PATH_TMP = Path("output_videos")
PATH_TMP.mkdir(parents=True, exist_ok=True)

def get_video_duration_ffmpeg(video_path):
    """
        Parameters
        ----------
        video_path : str
            The file path to the video file.

        Returns
        -------
        float
            The duration of the video in seconds.

        Raises
        ------
        ValueError
            If the output from ffprobe cannot be converted to a float.
        subprocess.SubprocessError
            If the ffprobe command fails to execute.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise subprocess.SubprocessError(result.stderr.strip())
    if not result.stdout.strip():
        raise ValueError(f"ffprobe returned no duration for {video_path}")

    return float(result.stdout.strip())


def mux_audio_video(cur_song_id, cur_ensemble):
    """
        This function combines audio tracks from a song database with a video file, 
        ensuring proper synchronization by adding silence at the beginning or end 
        of the audio as needed. The final output is a video file with the mixed 
        audio tracks.

        Parameters
        ----------
        cur_song_id : str
            The unique identifier of the song to be processed.
        cur_ensemble : dict
            A dictionary mapping part names (S/A/T/B) to instrument names.
            For example: {"S": "tp", "A": "fh", "T": "bar", "B": "tba"}.

        Raises
        ------
        FileNotFoundError
            If the video file corresponding to `cur_song_id` is not found.
        ValueError
            If the song ID does not exist in the song database or if the 
            audio and video durations cannot be synchronized.

        Notes
        -----
        - The function uses ffmpeg for muxing the audio and video.
        - Temporary audio files are created during the process and cleaned up afterward.
        - The function assumes the existence of a CSV file (`video_offsets.csv`) 
          containing offset information for each song.

        Examples
        --------
        >>> cur_song_id = "Anonymous_AusMeinesHerzensGrunde"
        >>> cur_ensemble = {1: "tp", 2: "fh", 3: "bar", 4: "tba"}
        >>> mux_audio_video(cur_song_id, cur_ensemble)
    """
    # Load the song database
    cbdb = SongDB()
    path_video = PATH_VIDEOS / f"{cur_song_id}.mp4"

    # get selected song
    cur_song = [s for s in cbdb.songs if s.id == cur_song_id][0]

    # filter track
    cur_tracks = []
    for cur_part in cur_ensemble.keys():
        cur_instrument = Instrument(cur_ensemble[cur_part])
        cur_tracks.extend([t for t in cur_song.tracks if t.part == cur_part and t.instrument == cur_instrument])

    print(cur_tracks)

    # mix tracks together
    cur_mix = MixerSimple(tracks=cur_tracks).get_mix()
    print(cur_mix["MIX"].shape)

    # Get the duration of the video
    dur_video = get_video_duration_ffmpeg(path_video)
    print(f"Video duration: {dur_video} seconds")
    dur_audio = len(cur_mix["MIX"]) / cur_mix["SAMPLERATE"]
    print(f"Audio duration: {dur_audio} seconds")

    # prepare the audio file
    df_offsets = pd.read_csv(PATH_VIDEO_OFFSETS, sep=";")
    cur_offset = df_offsets[df_offsets["song_id"] == cur_song_id]["offset"].values[0]
    print(f"Offset: {cur_offset} seconds")

    # prepend silence to the audio file
    silence_pre = np.zeros(int(cur_offset * cur_mix["SAMPLERATE"]))
    silence_post = np.zeros(int((dur_video - dur_audio - cur_offset) * cur_mix["SAMPLERATE"]))
    print(dur_video - dur_audio - cur_offset)
    out_wav = np.concatenate([silence_pre, cur_mix["MIX"], silence_post])
    path_audio = PATH_TMP / "output_silence.wav"
    print(f"Duration of output: {len(out_wav) / cur_mix['SAMPLERATE']} seconds")
    sf.write(path_audio, out_wav, cur_mix["SAMPLERATE"])

    # muxing
    path_output = PATH_TMP / f"{cur_song_id}_{"_".join(cur_ensemble.values())}.mp4"

    command = [
        "ffmpeg",
        "-i", path_video,
        "-i", path_audio,
        "-y",  # Overwrite output file if it exists
        "-c:v", "copy",  # Copy video without re-encoding
        "-c:a", "aac",   # Encode audio in AAC
        "-strict", "experimental",
        path_output
    ]

    subprocess.run(command)

    # cleanup
    path_audio.unlink()

def main():
    ENSEMBLES = {
        "Anonymous_AusMeinesHerzensGrunde": {"S": "tp", "A": "fh", "T": "bar", "B": "tba"},
        "Bach_IchStehAnDeinerKrippe": {"S": "fl", "A": "cl", "T": "bar", "B": "tba"},
        "Crueger_AufAufMeinHerzMitFreuden": {"S": "as", "A": "as", "T": "bs", "B": "bs"},
        "Drese_JesuGehVoran": {"S": "ob", "A": "fh", "T": "bar", "B": "bcl"},
        "Gesius_BefiehlDuDeineWege": {"S": "fh", "A": "fh", "T": "tb", "B": "tba"},
        "Gesius_DuFriedensfuerstHerrJesuChrist": {"S": "cl", "A": "cl", "T": "bcl", "B": "bcl"},
        "Jan_DuGrosserSchmerzensmann": {"S": "fl", "A": "tp", "T": "bar", "B": "bs"},
        "Telemann_DerLiebenSonneLichtUndPracht": {"S": "fh", "A": "fh", "T": "bar", "B": "bs"},
        "Vulpius_DieHelleSonnLeuchtJetztHerfuer": {"S": "ob", "A": "eh", "T": "bs", "B": "bs"},
        "Vulpius_ChristusDerIstMeinLeben": {"S": "bar", "A": "bar", "T": "bar", "B": "bar"},
    }

    for cur_song_id, cur_ensemble in ENSEMBLES.items():
        print(f"Processing {cur_song_id} with ensemble {cur_ensemble}")
        mux_audio_video(cur_song_id, cur_ensemble)

if __name__ == "__main__":
    main()
