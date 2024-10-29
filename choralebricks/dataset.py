from typing import Any, Optional, Union
import logging
import copy
from pydantic import BaseModel
from pathlib import Path
from enum import Enum, EnumMeta
from abc import ABC, abstractmethod
import numpy as np
import soundfile as sf


logger = logging.getLogger(__name__)

# class MetaEnum(EnumMeta):
#     def __contains__(cls, item):
#         try:
#             cls(item)
#         except ValueError:
#             return False
#         return True


# class StrEnum(str, Enum, metaclass=MetaEnum):
#     def __str__(self):
#         return str(self.value)


# class Instruments(StrEnum):
#     trumpet = "Trumpet"

NUM_VOICES = 4


class Track(BaseModel):
    """
    Represents a track and its metadata.
    """

    path_audio: Union[str, Path]
    path_f0: Optional[Union[str, Path]] = None
    path_score: Optional[Union[str, Path]] = None
    num_channels: int
    min_samples: int
    sample_rate: int
    voice: int
    instrument: str = None
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
        path_tracks = [f for f in tracks_dir.glob(f"*.{suffix}") if f.is_file()]

        for cur_path_tracks in path_tracks:
            logger.info(f"Adding track: {cur_path_tracks.name}...")
            file_info = sf.info(cur_path_tracks)

            voice, instrument = cur_path_tracks.stem.split("_")

            cur_track = Track(
                path_audio=cur_path_tracks,
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

    def __init__(self, root_dir: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.root_dir: Path = Path(root_dir)
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

        track_choice_ids = np.random.choice(len(self.song.tracks), size=num_voices, replace=False)

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
