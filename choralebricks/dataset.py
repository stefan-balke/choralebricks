import copy
import logging
import os
from abc import ABC, abstractmethod
from importlib.metadata import PackageNotFoundError, version as distribution_version
from itertools import product
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import numpy as np
import pandas as pd
import soundfile as sf
from pydantic import BaseModel, model_validator

from .constants import (INSTRUMENT_FROM_NAME, INSTRUMENTS_BRASS, INSTRUMENTS_WOODWIND,
                        Instrument, InstrumentType, Voices, VOICE_STRINGS)

logger = logging.getLogger(__name__)


def package_version() -> str:
    try:
        return distribution_version("choralebricks")
    except PackageNotFoundError:
        return "unknown"


PACKAGE_VERSION = package_version()


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
    path_sheet_music_mei: Optional[Union[str, Path]] = None
    path_sheet_music_pdf: Optional[Union[str, Path]] = None
    path_chords: Optional[Union[str, Path]] = None
    num_channels: int = 0
    min_samples: int = 0
    sample_rate: int = 0
    part: str = None
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
        return f"(P: {self.part}, I: {self.instrument})"


def optional_metadata_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def existing_path(path: Path) -> Optional[Path]:
    """Return ``path`` if it points at a file, otherwise ``None``."""
    return path if path.is_file() else None


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
                 dataset_type: str = "choralebricks",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.song_dir: Path = song_dir
        self.title: str = title
        self.composer: str = composer
        self.year: int = year
        self.dataset_type: str = dataset_type
        self.id: str = self.song_dir.name
        self.tracks: list[Track] = []
        self._current_index = 0

        # check if the song_dir exists
        # (otherwise, it is a dummy song for testing purposes)
        if self.song_dir.is_dir():
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
                want_part = VOICE_STRINGS[Voices(int(voice))]
            except (ValueError, KeyError) as exc:
                raise KeyError(f"Track key '{key}' is not in the correct format e.g. '01_tp'.") from exc

            for track in self.tracks:
                if track.part == want_part and track.instrument.value == inst:
                    return track
            raise KeyError(f"Track with id '{key}' not found.")
        elif isinstance(key, int):
            try:
                return self.tracks[key]
            except IndexError as exc:
                raise IndexError(f"Index '{key}' is out of range.") from exc
        else:
            raise TypeError("Key must be a string (track_id) or an integer (index).")

    def _resolve_score_paths(self) -> dict:
        """Resolve the per-song score / render file paths for the dataset type.

        The naming scheme is determined by ``dataset_type`` (no auto-detection):

        - ``"choralebricks"``: ``<id>.csv`` / ``.mid`` / ``.mei`` / ``.pdf``
        - ``"choralewind"``: ``<id>_01-preproc.csv`` / ``.mid`` / ``.mei`` / ``.pdf``

        MusicXML and chord annotations are optional and resolved by existence.
        """
        sd, sid = self.song_dir, self.id
        if self.dataset_type == "choralebricks":
            stem = sid
        elif self.dataset_type == "choralewind":
            stem = f"{sid}_01-preproc"
        else:
            raise ValueError(
                f"Unknown dataset type '{self.dataset_type}'. "
                "Expected 'choralebricks' or 'choralewind'."
            )

        return {
            "csv": existing_path(sd / f"{stem}.csv"),
            "midi": existing_path(sd / f"{stem}.mid"),
            "mei": existing_path(sd / f"{stem}.mei"),
            "pdf": existing_path(sd / f"{stem}.pdf"),
            "mxml": existing_path(sd / f"{sid}.musicxml"),
            "chords": existing_path(sd / "annotations" / "chords.csv"),
        }

    def __collect_tracks(self, suffix="wav"):
        tracks_dir = self.song_dir / "tracks_normalized"
        score_paths = self._resolve_score_paths()

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

            if not cur_path_f0.is_file():
                cur_path_f0 = None

            if not cur_path_notes.is_file():
                cur_path_notes = None

            cur_track = Track(
                song_id=self.id,
                path_audio=cur_path_tracks,
                path_f0=cur_path_f0,
                path_notes=cur_path_notes,
                path_sheet_music_csv=score_paths["csv"],
                path_sheet_music_midi=score_paths["midi"],
                path_sheet_music_mxml=score_paths["mxml"],
                path_sheet_music_mei=score_paths["mei"],
                path_sheet_music_pdf=score_paths["pdf"],
                path_chords=score_paths["chords"],
                num_channels=file_info.channels,
                min_samples=file_info.frames,
                sample_rate=file_info.samplerate,
                part=cur_meta_track["part"],
                instrument=INSTRUMENT_FROM_NAME[cur_meta_track["instrument"]],
                date=optional_metadata_value(cur_meta_track["date"]),
                performer=optional_metadata_value(cur_meta_track["performer"]),
                microphone=optional_metadata_value(cur_meta_track["microphone"]),
                room=optional_metadata_value(cur_meta_track["room"]),
            )
            self.tracks.append(cur_track)


class SongDB:
    """
    Represents the Song Database. Collects songs from a pre-defined folder structure.
    """

    def __init__(self, root_dir: str = None, type: str = "choralebricks", **kwargs) -> None:
        super().__init__(**kwargs)

        if type not in ("choralebricks", "choralewind"):
            raise ValueError(
                f"Unknown dataset type '{type}'. "
                "Expected 'choralebricks' or 'choralewind'."
            )
        self.dataset_type = type

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
            logger.info(f"Adding song {cur_meta_song['song_id']}...")
            cur_path_song = self.root_dir / cur_meta_song["song_id"]
            cur_song = Song(song_dir=cur_path_song,
                            composer=cur_meta_song["composer"],
                            title=cur_meta_song["title"],
                            year=cur_meta_song["year"],
                            dataset_type=self.dataset_type)
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

        parts: list[str] = [cur_track.part for cur_track in self.song.tracks]
        track_choice_ids: list[int] = []

        # for each part, draw a track
        for cur_part in set(parts):
            candidate_idcs: np.array = np.where(np.asarray(parts) == cur_part)[0]
            choice_id: int = int(np.random.choice(candidate_idcs))
            track_choice_ids.append(choice_id)

        # collate tracks
        self.song.tracks = [self.song.tracks[i] for i in track_choice_ids]


class EnsemblePermutations(Ensemble):
    def __init__(self, song: Song):
        self.song = song
        self.ensembles = list()
        self.tracks_by_part: dict = dict()

        self._categorize_tracks_byparts()

        # getting all the permutations as a cartesian product of all tracks
        # Note: Converting it to a list might get big, if more data is stored
        self._permutations: list[tuple[int]] = list(product(*self.tracks_by_part.values()))

    def _categorize_tracks_byparts(self):
        """
        Categorize the tracks into their respective part bucket (S, A, T, B).
        """
        # for each track, get the associated part
        parts: list[str] = [cur_track.part for cur_track in self.song.tracks]

        # for each part, collect the track object and add to the list in the dict
        for cur_part in set(parts):
            candidate_idcs: np.array = np.where(np.asarray(parts) == cur_part)[0]

            # init list in the list which will hold the objects
            self.tracks_by_part[cur_part] = list()

            for cur_idc in candidate_idcs:
                self.tracks_by_part[cur_part].append(cur_idc)

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

        # Tracks could differ in samples, we assume that the start position is correct
        min_samples = min(len(audio) for audio in track_audio)
        track_audio = np.asarray([audio[:min_samples] for audio in track_audio])
        track_audio = (10 ** (self.gains / 20))[:, np.newaxis] * track_audio
        track_audio = track_audio / track_audio.shape[0]  # all equal amplitude from original file

        self.mix = np.sum(track_audio, axis=0)

        # Check for clipping
        if (self.mix.min() < -1.0) or (self.mix.max() > 1.0):
            logger.warning("Clipping detected in output mix. Please check the gains.")

        return {"MIX": self.mix, "TRACKS": track_audio, "SAMPLERATE": track_samplerates[0]}
