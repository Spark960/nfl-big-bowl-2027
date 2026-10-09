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


def angular_rate(dir_series: pd.Series, dt: float = 0.1) -> pd.Series:
    """Signed rate of direction change in degrees/second."""
    return frame_angular_change(dir_series) / dt


def smooth_series(series: pd.Series, window: int = 3) -> pd.Series:
    """Rolling mean smoothing for 10 Hz tracking series."""
    return series.rolling(window=window, min_periods=1, center=True).mean()


def detect_turn_events(
    attempt_df: pd.DataFrame,
    threshold: float = 30.0,
    min_total_angle: float = 45.0,
    min_turn_speed: float = 1.3,
    active_speed_floor: float = 0.5,
    dt: float = 0.1,
) -> list[dict]:
    """Detect turn events within a single sorted drill attempt DataFrame.

    Identifies consecutive frames inside the active drill window (s > active_speed_floor)
    where abs(angular_rate(dir)) > threshold and s > min_turn_speed, and filters to
    turns with cumulative angle change >= min_total_angle and at least 3 pre-turn frames.
    """
    if len(attempt_df) < 6:
        return []

    s = attempt_df["s"].to_numpy(dtype=float)
    moving = np.where(s > active_speed_floor)[0]
    if len(moving) < 6:
        return []
    start_win, end_win = int(moving[0]), int(moving[-1])

    dir_change = frame_angular_change(attempt_df["dir"]).fillna(0.0).to_numpy(dtype=float)
    rate = dir_change / dt

    is_turn = np.zeros(len(s), dtype=bool)
    is_turn[start_win : end_win + 1] = (np.abs(rate[start_win : end_win + 1]) > threshold) & (
        s[start_win : end_win + 1] > min_turn_speed
    )

    events: list[dict] = []
    in_turn = False
    st = 0
    for i in range(len(is_turn) + 1):
        val = bool(is_turn[i]) if i < len(is_turn) else False
        if val and not in_turn:
            in_turn = True
            st = i
        elif not val and in_turn:
            in_turn = False
            ed = i - 1
            total_angle = float(np.sum(np.abs(dir_change[st : ed + 1])))
            if total_angle >= min_total_angle and st >= 3:
                events.append(
                    {
                        "start_frame": st,
                        "end_frame": ed,
                        "total_angle_change": total_angle,
                    }
                )
    return events

