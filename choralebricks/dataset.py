import copy
import logging
import os
from abc import ABC, abstractmethod
from itertools import product
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import numpy as np
import pandas as pd
import soundfile as sf
from pydantic import BaseModel, model_validator

from .constants import (INSTRUMENTS_BRASS, INSTRUMENTS_WOODWIND, Instrument,
                        InstrumentType)

logger = logging.getLogger(__name__)


class Track(BaseModel):
    """
    Represents a track and its metadata.
    """

    song_id: str = None
    path_audio: Union[str, Path] = None
    path_f0: Optional[Union[str, Path]] = None
    path_notes: Optional[Union[str, Path]] = None
    path_sheet_music_csv: Optional[Union[str, Path]] = None
    path_sheet_music_midi: Optional[Union[str, Path]] = None
    path_sheet_music_mxml: Optional[Union[str, Path]] = None
    path_chords: Optional[Union[str, Path]] = None
    num_channels: int = 0
    min_samples: int = 0
    sample_rate: int = 0
    voice: int = 0
    instrument: Instrument
    instrument_type: InstrumentType = None
    date: Optional[str] = None
    performer: Optional[str] = None
    microphone: Optional[str] = None
    room: Optional[str] = None

    @model_validator(mode="before")
    def set_instrument_type(cls, values):
        """Set instrument_type based on instrument."""
        instrument = values.get("instrument")
        if instrument in INSTRUMENTS_BRASS:
            values["instrument_type"] = InstrumentType.BRASS
        elif instrument in INSTRUMENTS_WOODWIND:
            values["instrument_type"] = InstrumentType.WOODWIND
        return values

    def __repr__(self):
        return f"(V: {self.voice}, I: {self.instrument})"


class Song:
    """
    Represents the information about a song, including its directory, tracks, and associated metadata.

    Attributes
    ----------
    id : str
        Identifier of the song, typically the folder name.
    song_dir : Path
        Root directory of the song.
    tracks : list[Track]
        List of associated multi-tracks for the song.
    score : tbd
        Score representation of the song (to be defined).
    alignment : tbd
        Global alignment from score to audio (to be defined).

    Methods
    -------
    __repr__():
        Returns a string representation of the song, including its ID and the number of tracks.
    __len__():
        Returns the number of tracks in the song.
    __iter__():
        Initializes the iterator for the tracks.
    __next__():
        Returns the next track in the iteration.
    __getitem__(key: Union[int, str]) -> Track:
        Retrieves a track by its index or string identifier.
    __collect_tracks(suffix="wav"):
        Collects and initializes track objects from the song's directory.
    """

    def __init__(self,
                 song_dir: str,
                 title: str = None,
                 composer: str = None,
                 year: int = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.song_dir: Path = song_dir
        self.title: str = title
        self.composer: str = composer
        self.year: int = year
        self.id: str = self.song_dir.name
        self.tracks: list[Track] = []
        self._current_index = 0

        self.df_meta_tracks = pd.read_csv(self.song_dir.parent / "metadata_tracks.csv", sep=";")
        self.df_meta_tracks = self.df_meta_tracks[self.df_meta_tracks["song_id"] == self.id]

        self.__collect_tracks()

    def __repr__(self):
        return f"<{self.id}, {self.composer}, #Tracks: {len(self.tracks)}>"

    def __len__(self):
        return len(self.tracks)

    def __iter__(self) -> Iterator[Track]:
        self._current_index = 0
        return self

    def __next__(self) -> Track:
        if self._current_index < len(self.tracks):
            track = self.tracks[self._current_index]
            self._current_index += 1
            return track
        raise StopIteration

    def __getitem__(self, key: Union[int, str]) -> Track:
        if isinstance(key, str):
            try:
                voice, inst = key.split("_")
                voice = int(voice)
            except ValueError as exc:
                raise KeyError(f"Track key '{key}' is not in the correct format e.g. '01_tp'.") from exc

            for track in self.tracks:
                if int(track.voice) == int(voice) and track.instrument.value == inst:
                    return track
            raise KeyError(f"Track with id '{key}' not found.")
        elif isinstance(key, int):
            try:
                return self.tracks[key]
            except IndexError as exc:
                raise IndexError(f"Index '{key}' is out of range.") from exc
        else:
            raise TypeError("Key must be a string (track_id) or an integer (index).")

    def __collect_tracks(self, suffix="wav"):
        tracks_dir = self.song_dir / "tracks_normalized"

        # get all the audio files
        for _, cur_meta_track in self.df_meta_tracks.iterrows():
            logger.info(f"Adding track: {cur_meta_track.path_audio}...")
            cur_path_tracks = tracks_dir / cur_meta_track.path_audio

            try:
                assert cur_path_tracks.is_file()
            except AssertionError:
                logger.error(f"File {cur_path_tracks} not found.")

            file_info = sf.info(cur_path_tracks)

            cur_path_f0 = self.song_dir / "annotations" / cur_meta_track["path_f0"]
            cur_path_notes = self.song_dir / "annotations" / cur_meta_track["path_notes"]
            cur_path_sheet_music_csv = self.song_dir / f"{self.id}.csv"
            cur_path_sheet_music_midi = self.song_dir / f"{self.id}.mid"
            cur_path_sheet_music_mxml = self.song_dir / f"{self.id}.musicxml"
            cur_path_chords = self.song_dir / "annotations" / f"chords.csv"

            if not cur_path_f0.is_file():
                cur_path_f0 = None

            if not cur_path_notes.is_file():
                cur_path_notes = None

            cur_track = Track(
                song_id=self.id,
                path_audio=cur_path_tracks,
                path_f0=cur_path_f0,
                path_notes=cur_path_notes,
                path_sheet_music_csv=cur_path_sheet_music_csv,
                path_sheet_music_midi=cur_path_sheet_music_midi,
                path_sheet_music_mxml=cur_path_sheet_music_mxml,
                path_chords=cur_path_chords,
                num_channels=file_info.channels,
                min_samples=file_info.frames,
                sample_rate=file_info.samplerate,
                voice=int(cur_meta_track["voice"]),
                instrument=Instrument(cur_meta_track["instrument"]),
                date=cur_meta_track["date"],
                performer=cur_meta_track["performer"],
                microphone=cur_meta_track["microphone"],
                room=cur_meta_track["room"],
            )
            self.tracks.append(cur_track)


class SongDB:
    """
    Represents the Song Database. Collects songs from a pre-defined folder structure.
    """

    def __init__(self, root_dir: str = None, **kwargs) -> None:
        super().__init__(**kwargs)

        if root_dir is None:
            if "CHORALEDB_PATH" in os.environ:
                self.root_dir = Path(os.environ["CHORALEDB_PATH"])
                print(self.root_dir)
            else:
                raise RuntimeError("Variable `CHORALEDB_PATH` has not been set.")
        else:
            self.root_dir = Path(root_dir).expanduser()

        self.songs: list[Song] = []
        self.__collect_songs()
        self._current_index = 0

    def __len__(self):
        return len(self.songs)

    def __iter__(self) -> Iterator[Song]:
        self._current_index = 0
        return self

    def __next__(self) -> Song:
        if self._current_index < len(self.songs):
            song = self.songs[self._current_index]
            self._current_index += 1
            return song
        raise StopIteration

    def __getitem__(self, key: Union[int, str]) -> Song:
        if isinstance(key, str):
            for song in self.songs:
                if song.id == key:
                    return song
            raise KeyError(f"Song with id '{key}' not found.")
        elif isinstance(key, int):
            try:
                return self.songs[key]
            except IndexError as exc:
                raise IndexError(f"Index '{key}' is out of range.") from exc
        else:
            raise TypeError("Key must be a string (song_id) or an integer (index).")

    def __collect_songs(self):
        df_meta_songs = pd.read_csv(self.root_dir / "metadata_songs.csv", sep=";")

        for _, cur_meta_song in df_meta_songs.iterrows():
            logger.info(f"Adding song {cur_meta_song["song_id"]}...")
            cur_path_song = self.root_dir / cur_meta_song["song_id"]
            cur_song = Song(song_dir=cur_path_song,
                            composer=cur_meta_song["composer"],
                            title=cur_meta_song["title"],
                            year=cur_meta_song["year"])
            self.songs.append(cur_song)


class Ensemble(ABC):
    """
    Abstract Base Class for an ensemble selector.

    Don't use directly, only inherit.
    """

    @abstractmethod
    def filter_tracks(self):
        pass


class EnsembleRandom(Ensemble):
    def __init__(self, song: Song):
        self.song = copy.deepcopy(song)
        self.filter_tracks()

    def get_tracks(self) -> list[Track]:
        return self.song.tracks

    def filter_tracks(self):
        # copy of the song with randomly fitered tracks
        logger.info(f"Track selection in {self.song.id}")

        voices: list[int] = [cur_track.voice for cur_track in self.song.tracks]
        track_choice_ids: list[int] = []

        # for each voice, draw a track
        for cur_voice in set(voices):
            candidate_idcs: np.array = np.where(np.asarray(voices) == cur_voice)[0]
            choice_id: int = int(np.random.choice(candidate_idcs, size=1))
            track_choice_ids.append(choice_id)

        # collate tracks
        self.song.tracks = [self.song.tracks[i] for i in track_choice_ids]


class EnsemblePermutations(Ensemble):
    def __init__(self, song: Song):
        self.song = song
        self.ensembles = list()
        self.tracks_by_voice: dict = dict()

        self._categorize_tracks_byvoices()

        # getting all the permutations as a cartesian product of all tracks
        # Note: Converting it to a list might get big, if more data is stored
        self._permutations: list[tuple[int]] = list(product(*self.tracks_by_voice.values()))

    def _categorize_tracks_byvoices(self):
        """
        Categorize the voices in the respective bucket 1, 2, 3, or 4, based on the filename.
        """
        # for each track, get the associated voice
        voices: list[int] = [cur_track.voice for cur_track in self.song.tracks]

        # for each voice, collect the track object and add to the list in the dict
        for cur_voice in set(voices):
            candidate_idcs: np.array = np.where(np.asarray(voices) == cur_voice)[0]

            # init list in the list which will hold the objects
            self.tracks_by_voice[str(cur_voice)] = list()

            for cur_idc in candidate_idcs:
                self.tracks_by_voice[str(cur_voice)].append(cur_idc)

    def filter_tracks(self, track_choice_ids):
        """
        Filter the tracks based on the chosen ensemble permutation.
        """
        # collate tracks
        return [self.song.tracks[i] for i in track_choice_ids]

    def __getitem__(self, index) -> list[Track]:
        track_choice_ids = self._permutations[index]

        # filter the tracks to the permuation selection
        selected_tracks = self.filter_tracks(track_choice_ids=track_choice_ids)

        logger.info(
            f"Returning ensemble: "
            f"{selected_tracks[0].instrument}, "
            f"{selected_tracks[1].instrument}, "
            f"{selected_tracks[2].instrument}, "
            f"{selected_tracks[3].instrument}"
        )

        return selected_tracks

    def __len__(self):
        return len(self._permutations)

    def __repr__(self):
        return f"Indexed instrument permutations with {len(self)} items."


class Mixer(ABC):
    """
    Abstract Base Class for a mixer.

    Don't use directly, only inherit.
    """

    @abstractmethod
    def get_mix(self):
        pass


class MixerSimple(Mixer):
    """
    Simple track mixer.

    Attributes:
        tracks (list[Track]): List of associated multi-tracks.
        gains (Optional[list[float]]): Gain levels (in dB) per track (defaults to 0 dB if not provided).
    """
    def __init__(self,
                 tracks: list[Track],
                 gains: Optional[list[float]] = None):
        self.tracks = tracks

        if gains is None:
            self.gains = len(self.tracks) * [0.0]
        else:
            self.gains = gains

        self.gains = np.asarray(self.gains)


    def get_mix(self):
        """Mix tracks together by sum(tracks)/num_tracks"""
        logger.info("Mixing...")
        track_audio = []

        track_samplerates = [cur_track.sample_rate for cur_track in self.tracks]
        try:
            assert all(x == track_samplerates[0] for x in track_samplerates) if track_samplerates else True
        except AssertionError:
            logger.error("Not all track samplerates are equal!")

        for cur_track in self.tracks:
            audio, _ = sf.read(cur_track.path_audio)
            track_audio.append(audio)

        # TODO: tracks could differ in samples, we assume that the start position is correct
        # quick fix: Take shortest number of samples from all tracks
        track_audio = np.asarray(track_audio)
        track_audio = (10 ** (self.gains / 20))[:, np.newaxis] * track_audio
        track_audio = track_audio / track_audio.shape[0]  # all equal amplitude from original file

        self.mix = np.sum(track_audio, axis=0)

        # Check for clipping
        if (self.mix.min() < -1.0) or (self.mix.max() > 1.0):
            logger.warning("Clipping detected in output mix. Please check the gains.")

        return {"MIX": self.mix, "TRACKS": track_audio, "SAMPLERATE": track_samplerates[0]}
