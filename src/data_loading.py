"""Reusable data loading helpers with chunked filtering for large tracking files."""

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "nfl-big-data-bowl-2027"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DL_POSITIONS = ["DE", "OLB", "DT", "NT"]
DL_LINED_UP_POSITIONS = ["EDGE", "INTERIOR_LINE", "DE", "DT", "OLB", "NT"]


def load_players(dl_only: bool = False, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load players.csv, optionally filtering to DL pass rushers (DE, OLB, DT, NT)."""
    df = pd.read_csv(data_dir / "players.csv")
    if dl_only:
        df = df[df["nfl_position"].isin(DL_POSITIONS)].copy()
    return df


def load_combine_results(
    nfl_ids: Optional[Iterable[int]] = None, data_dir: Path = DATA_DIR
) -> pd.DataFrame:
    """Load combine_results.csv, optionally filtering by nfl_id."""
    df = pd.read_csv(data_dir / "combine_results.csv")
    if nfl_ids is not None:
        id_set = set(nfl_ids)
        df = df[df["nfl_id"].isin(id_set)].copy()
    return df


def load_career_successes(
    nfl_ids: Optional[Iterable[int]] = None, data_dir: Path = DATA_DIR
) -> pd.DataFrame:
    """Load player_career_successes.csv, optionally filtering by nfl_id."""
    df = pd.read_csv(data_dir / "player_career_successes.csv")
    if nfl_ids is not None:
        id_set = set(nfl_ids)
        df = df[df["nfl_id"].isin(id_set)].copy()
    return df


def load_games(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load games.csv."""
    return pd.read_csv(data_dir / "games.csv")


def load_combine_tracking(
    nfl_ids: Optional[Iterable[int]] = None,
    drill_types: Optional[Iterable[str]] = None,
    entity_type: Optional[str] = None,
    chunksize: int = 100_000,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Load combine_tracking.csv with optional chunked filtering."""
    path = data_dir / "combine_tracking.csv"
    id_set = set(nfl_ids) if nfl_ids is not None else None
    drill_set = set(drill_types) if drill_types is not None else None

    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        mask = pd.Series(True, index=chunk.index)
        if id_set is not None:
            mask &= chunk["nfl_id"].isin(id_set)
        if drill_set is not None:
            mask &= chunk["drill_type"].isin(drill_set)
        if entity_type is not None:
            mask &= chunk["entity_type"] == entity_type
        filtered = chunk[mask]
        if not filtered.empty:
            chunks.append(filtered)

    if not chunks:
        return pd.read_csv(path, nrows=0)
    return pd.concat(chunks, ignore_index=True)


def load_player_play(
    nfl_ids: Optional[Iterable[int]] = None,
    lined_up_positions: Optional[Iterable[str]] = None,
    chunksize: int = 100_000,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Load player_play.csv with optional chunked filtering by nfl_id and lined_up_position."""
    path = data_dir / "player_play.csv"
    id_set = set(nfl_ids) if nfl_ids is not None else None
    pos_set = set(lined_up_positions) if lined_up_positions is not None else None

    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        mask = pd.Series(True, index=chunk.index)
        if id_set is not None:
            mask &= chunk["nfl_id"].isin(id_set)
        if pos_set is not None:
            mask &= chunk["lined_up_position"].isin(pos_set)
        filtered = chunk[mask]
        if not filtered.empty:
            chunks.append(filtered)

    if not chunks:
        return pd.read_csv(path, nrows=0)
    return pd.concat(chunks, ignore_index=True)


GAME_TRACKING_DTYPES = {
    "game_id": "int64",
    "play_id": "int64",
    "nfl_id": "int64",
    "time": "object",
    "x": "float64",
    "y": "float64",
    "s": "float64",
    "a": "float64",
    "dis": "float64",
    "o": "float64",
    "dir": "float64",
    "event": "object",
}


def load_game_tracking(
    seasons: Iterable[int] = (2023,),
    game_ids: Optional[Iterable[int]] = None,
    play_ids: Optional[Iterable[int]] = None,
    nfl_ids: Optional[Iterable[int]] = None,
    chunksize: int = 500_000,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Lazy-load game_tracking_{season}.csv files with chunked filtering to avoid OOM."""
    game_set = set(game_ids) if game_ids is not None else None
    play_set = set(play_ids) if play_ids is not None else None
    id_set = set(nfl_ids) if nfl_ids is not None else None

    chunks = []
    first_path = None
    for season in seasons:
        path = data_dir / f"game_tracking_{season}.csv"
        if first_path is None:
            first_path = path
        for chunk in pd.read_csv(path, chunksize=chunksize, dtype=GAME_TRACKING_DTYPES):
            mask = pd.Series(True, index=chunk.index)
            if id_set is not None:
                mask &= chunk["nfl_id"].isin(id_set)
            if game_set is not None:
                mask &= chunk["game_id"].isin(game_set)
            if play_set is not None:
                mask &= chunk["play_id"].isin(play_set)
            filtered = chunk[mask]
            if not filtered.empty:
                chunks.append(filtered)

    if not chunks:
        return pd.read_csv(first_path, nrows=0) if first_path else pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)

