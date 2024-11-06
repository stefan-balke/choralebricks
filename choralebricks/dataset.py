from typing import Any, Optional, Union
import logging
import os
import copy
from pydantic import BaseModel
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np
import soundfile as sf

from .constants import Instrument, NUM_VOICES


logger = logging.getLogger(__name__)

class Track(BaseModel):
    """
    Represents a track and its metadata.
    """

    path_audio: Union[str, Path]
    path_f0: Optional[Union[str, Path]] = None
    path_notes: Optional[Union[str, Path]] = None
    num_channels: int
    min_samples: int
    sample_rate: int
    voice: int
    instrument: Instrument = None
    player_id: Optional[str] = None
    microphone: Optional[str] = None
    room: Optional[str] = None


class Song:
    """
    Represents the information about a song.

    Attributes:
        id (str): Identifier (usually the folder name).
        song_dir (Path): Root directory of the song.
        tracks (list[Track]): List of associated multi-tracks.
        score (tbd): Score representation of the song.
        alignment (tbd): Global alignment from score to audio.
    """

    def __init__(self, song_dir: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.song_dir: Path = song_dir
        self.id: str = self.song_dir.name
        self.tracks: list[Track] = []

        self.collect_tracks()

    def __repr__(self):
        return f"{self.id}, #Tracks: {len(self.tracks)}"

    def collect_tracks(self, suffix="wav"):
        tracks_dir = self.song_dir / "tracks"
        
        # get all the audio files
        path_tracks = [f for f in tracks_dir.glob(f"*.{suffix}") if f.is_file()]

        for cur_path_tracks in path_tracks:
            logger.info(f"Adding track: {cur_path_tracks.name}...")
            file_info = sf.info(cur_path_tracks)

            # extract voice and instrument from file name
            voice, instrument = cur_path_tracks.stem.split("_")

            cur_path_f0 = self.song_dir / "annotations" / f"{cur_path_tracks.stem}_f0.csv"
            cur_path_notes = self.song_dir / "annotations" / f"{cur_path_tracks.stem}_notes.csv"

            if not cur_path_f0.is_file():
                cur_path_f0 = None

            if not cur_path_notes.is_file():
                cur_path_notes = None

            cur_track = Track(
                path_audio=cur_path_tracks,
                path_f0=cur_path_f0,
                path_notes=cur_path_notes,
                num_channels=file_info.channels,
                min_samples=file_info.frames,
                sample_rate=file_info.samplerate,
                voice=int(voice),
                instrument=instrument,
            )
            self.tracks.append(cur_track)


class SongDB:
    """
    Represents the Song Database. Collects songs from a pre-defined folder structure.
    """

    def __init__(
        self,
        root_dir: str=None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        if root_dir is None:
            if "CHORALEDB_PATH" in os.environ:
                self.root_dir = os.environ["CHORALEDB_PATH"]
            else:
                raise RuntimeError("Variable `CHORALEDB_PATH` has not been set.")
        else:
            self.root_dir = Path(root_dir).expanduser()

        self.songs: list[Song] = []
        self.collect_songs()

    def collect_songs(self):
        path_songs = [f for f in self.root_dir.glob("*") if f.is_dir()]

        for cur_path_song in path_songs:
            logger.info(f"Adding song {cur_path_song}...")
            cur_song = Song(song_dir=cur_path_song)
            self.songs.append(cur_song)


class TrackSelector(ABC):
    """
    Abstract Base Class for a track selector.

    Don't use directly, only inherit.
    """

    @abstractmethod
    def filter_tracks(self):
        pass


class TrackSelectorRandom(TrackSelector):
    def __init__(
        self,
        song: Song,
    ):
        self.song = copy.deepcopy(song)
        self.filter_tracks()

    def filter_tracks(self, num_voices=NUM_VOICES):
        # copy of the song with randomly fitered tracks
        logger.info(f"Filtering {self.song.id}")

        voices: list[int] = [cur_track.voice for cur_track in self.song.tracks]
        track_choice_ids: list[int] = []

        # for each voice, draw a track
        for cur_voice in set(voices):
            candidate_idcs: np.array = np.where(np.asarray(voices) == cur_voice)[0]
            choice_id: int = int(np.random.choice(candidate_idcs, size=1))
            track_choice_ids.append(choice_id)

        # collate tracks
        self.song.tracks = [self.song.tracks[i] for i in track_choice_ids]


class Mixer(ABC):
    """
    Abstract Base Class for a mixer.

    Don't use directly, only inherit.
    """

    @abstractmethod
    def get_mix(self):
        pass

    # def load_audio():
    #     audio, sr = sf.read()


class MixerSimple(Mixer):
    def __init__(
        self,
        song: Song,
    ):
        self.song = song

    def get_mix(self):
        """Mix tracks together by sum(tracks)/num_tracks"""
        logger.info("Mixing...")
        track_audio = []

        track_samplerates = [cur_track.sample_rate for cur_track in self.song.tracks]
        try:
            assert all(x == track_samplerates[0] for x in track_samplerates) if track_samplerates else True
        except AssertionError:
            logger.error("Not all track samplerates are equal!")

        for cur_track in self.song.tracks:
            audio, _ = sf.read(cur_track.path_audio)
            track_audio.append(audio)

        # TODO: tracks could differ in samples, we assume that the start position is correct
        # quick fix: Take shortest number of samples from all tracks
        track_audio = np.asarray(track_audio)
        track_audio = track_audio / track_audio.shape[0]  # all equal amplitude from original file

        # TODO: Add clipping protection?

        self.mix = np.sum(track_audio, axis=0)

        return {"MIX": self.mix, "TRACKS": track_audio, "SAMPLERATE": track_samplerates[0]}
