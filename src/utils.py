"""Coordinate math and angular signal helpers."""

import numpy as np
import pandas as pd


def angular_diff(a: np.ndarray | pd.Series | float, b: np.ndarray | pd.Series | float):
    """Shortest signed difference (a - b) in degrees within [-180, 180]."""
    return (a - b + 180.0) % 360.0 - 180.0


def frame_angular_change(dir_series: pd.Series) -> pd.Series:
    """Signed frame-to-frame direction change in degrees (handles 0/360 wrap)."""
    prev = dir_series.shift(1)
    return angular_diff(dir_series, prev)
