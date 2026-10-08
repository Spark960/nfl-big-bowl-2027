# Data Dictionary — NFL Side

Covers: `player_career_successes.csv`, `games.csv`, `player_play.csv`, `game_tracking_*.csv`

---

## File 4: `player_career_successes.csv`

Cumulative career volume statistics, snap counts, and accolades for all 510 prospects.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `nfl_id` | int64 | 55867 | Player ID → `players.csv`. |
| `career_offensive_snaps` | int64 | 0 | Cumulative regular-season + playoff offensive snaps. |
| `career_defensive_snaps` | int64 | 1884 | Cumulative regular-season + playoff defensive snaps. |
| `career_special_teams_snaps` | int64 | 92 | Cumulative special teams snaps. |
| `career_games_active` | int64 | 51 | Total regular-season games on active roster. |
| `career_games_started` | int64 | 44 | Total regular-season games started. |
| `ap_all_pro_1st_team` | int64 | 1 | Career AP First-Team All-Pro selections. |
| `ap_all_pro_2nd_team` | int64 | 0 | Career AP Second-Team All-Pro selections. |
| `pro_bowl_original_ballot` | int64 | 1 | Career original-ballot Pro Bowl selections (no injury replacements). |

---

## File 5: `player_play.csv` (64 columns)

Per-snap NGS + play-by-play metrics for the 510-player rookie cohort. **316,338 records** across 2023–2025.

### A. Play Context & Identifiers

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `game_id` | int64 | 2023091801 | 10-digit game ID → `games.csv`. |
| `play_id` | int64 | 56 | Play ID within the game. |
| `team_abbr` | str | BAL | Player's team (3-letter). |
| `nfl_id` | int64 | 55976 | Player ID → `players.csv`. |
| `lined_up_position` | str | T | Position aligned on this play (WR, CB, T, G, C, DE, DT, TE, FS, SS, OLB). |
| `play_description` | str | (15:00) P.Mahomes pass... | Official play-by-play description. |
| `quarter` | int64 | 1 | Quarter (1–4, 5 = OT). |
| `down` | int64 | 1 | Current down (1–4). |
| `yards_to_go` | int64 | 10 | Yards to first down / TD. |
| `possession_team` | str | CLE | Offensive team (3-letter). |
| `yardline_side` | str | CLE | Team side of field where ball spotted. |
| `yardline_number` | int64 | 25 | Distance to nearest goal line (1–50). |
| `game_clock` | str | 15:00 | Game clock remaining (MM:SS). |
| `pre_snap_home_score` | int64 | 0 | Home team score before snap. |
| `pre_snap_visitor_score` | int64 | 0 | Visitor score before snap. |
| `play_direction` | str | left | Offensive play direction (left/right). |

### B. Win Probability & Expected Points

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `pre_snap_home_team_win_probability` | float64 | 0.4237 | Home team win probability pre-snap. |
| `pre_snap_visitor_team_win_probability` | float64 | 0.5763 | Visitor win probability pre-snap. |
| `home_team_win_probability_added` | float64 | 0.2210 | Change in home WP from the play. |
| `visitor_team_win_probility_added` | float64 | -0.2210 | Change in visitor WP from the play. *(Note: typo "probility" is in original data.)* |
| `expected_points_added` | float64 | -8.459 | Net EPA generated on the play. |
| `expected_points` | float64 | 1.459 | Expected points of drive state pre-snap. |

### C. Schemes, Formations & Play Results

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `offense_formation` | str | EMPTY | Pre-snap formation (SHOTGUN, SINGLEBACK, EMPTY, I_FORM, PISTOL, JUMBO). |
| `receiver_alignment` | str | 3x2 | WR alignment distribution (3x1, 2x2, 3x2, 1x1, 4x1). |
| `pass_result` | str | IN | Pass outcome: C=Complete, I=Incomplete, S=Sack, IN=Interception, R=Scramble. |
| `pass_length` | float64 | 5.0 | Air yards past LOS (negative = behind LOS). |
| `play_nullified_by_penalty` | str | N | Y if play wiped out by penalty. |
| `penalty_yards` | float64 / null | null | Penalty yardage enforced. |
| `pre_penalty_yards_gained` | int64 | 0 | Gross yards before penalty. |
| `yards_gained` | int64 | 0 | Official net yards gained. |
| `team_coverage_man_zone` | str | ZONE_COVERAGE | Primary defensive coverage (MAN_COVERAGE, ZONE_COVERAGE). |
| `team_coverage_type` | str | COVER_6_ZONE | Specific coverage shell (COVER_0, COVER_1, COVER_2, COVER_3, COVER_4, COVER_6_ZONE, PREVENT). |
| `in_motion_at_ball_snap` | bool | False | True if player in pre-snap motion at snap. |

### D. Receiver & Ball Carrier Metrics

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `target` | bool | False | True if player was intended pass target. |
| `rec_yards` | float64 | 14.0 | Receiving yards on the play. |
| `rush_yards` | float64 / null | null | Rushing yards on the play. |
| `yards_after_catch` | float64 | 6.2 | Yards after catch (YAC). |
| `fumble` | float64 | 0.0 | 1.0 if fumbled. |
| `fumble_lost` | float64 | 0.0 | 1.0 if fumble recovered by opponent. |
| `route_ran` | str | SLANT | Route type (GO, OUT, SLANT, CROSS, POST, CORNER, HITCH, SCREEN, FLAT, WHEEL). |
| `separation_at_pass_forward` | float64 | 2.84 | Yards to nearest defender at throw. |
| `cushion` | float64 | 6.15 | Pre-snap WR–defender distance (yards). |
| `expected_yards_after_catch` | float64 | 4.1 | NGS expected YAC model prediction. |

### E. Offensive Line & Pass Protection Metrics

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `dropback_duration` | float64 | 1.835 | Snap to pass release/sack/pressure (seconds). |
| `extended_sack_allowed` | float64 | 0.0 | Sacks allowed on extended dropbacks (>4.0s). |
| `pass_rushers_encountered` | float64 | 1.0 | Distinct pass rushers engaged by the OL. |
| `peak_pressure_probability_allowed` | float64 | 0.1975 | Peak estimated pressure probability allowed. |
| `pressure_allowed` | bool | False | True if OL allowed a pressure (hurry/hit/sack). |
| `sack_allowed` | float64 | 0.0 | Sacks charged (1.0 solo, 0.5 shared). |
| `time_to_pressure_allowed` | float64 | 2.45 | Seconds from snap until OL allowed pressure. |

### F. Defensive Pass Rush & Tackle Metrics

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `blitzing` | bool | False | True if defender was blitzing. |
| `player_get_off` | float64 | 0.742 | Seconds from snap until rusher crosses LOS. |
| `sack` | float64 | 1.0 | 1.0 for sack (0.5 shared). |
| `tackle` | float64 | 1.0 | 1.0 for solo tackle. |
| `assist` | float64 | 0.0 | 1.0 for assisted tackle. |
| `caused_forced_fumble` | float64 | 0.0 | 1.0 if forced a fumble. |
| `recovered_fumble` | float64 | 0.0 | 1.0 if recovered a fumble. |
| `tackle_for_loss` | float64 | 1.0 | 1.0 if tackle behind LOS. |
| `time_to_pressure` | float64 | 2.18 | Seconds from snap to generating pressure. |
| `time_to_qb_hurry` | float64 | 2.80 | Seconds from snap to forcing QB hurry. |
| `coverage_assignment` | str | MAN | Pre-snap coverage assignment (MAN, DEEP_THIRD, FLAT, HOOK_CURL). |
| `coverage_assignment_at_snap` | str | MAN | Coverage assignment updated at snap (post-motion). |
| `quick_pressure` | float64 / null | null | 1.0 if pressure within 2.50s of snap. |
| `unblocked_pressure` | float64 / null | null | 1.0 if QB pressured through gap without being blocked. |

---

## File 6: `games.csv`

Schedule metadata for 1,002 NFL games across 2023–2025.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `game_id` | int64 | 2023090700 | 10-digit game ID (YYYYMMDD##). **Primary key.** |
| `game_key` | int64 | 59173 | Historical NFL game key. |
| `season` | int64 | 2023 | NFL season year. |
| `season_type` | str | REG | Season type: `REG` (Regular) or `POST` (Playoffs). |
| `week` | int64 | 1 | Week number (1–18). |
| `home_team_abbr` | str | KC | Home team (3-letter). |
| `visitor_team_abbr` | str | DET | Visiting team (3-letter). |

---

## Files 7–9: `game_tracking_2023.csv`, `game_tracking_2024.csv`, `game_tracking_2025.csv`

10 Hz in-game optical tracking for all 510 rookie cohort prospects per season.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `game_id` | int64 | 2024080952 | Game ID → `games.csv`. |
| `play_id` | int64 | 3379 | Play ID → `player_play.csv`. |
| `nfl_id` | int64 | 57367 | Player ID → `players.csv`. |
| `time` | str | 2024-08-10T01:30:31.800 | ISO 8601 timestamp (every 0.10s). |
| `x` | float64 | 87.09 | Horizontal position (**yards**, 0–120). |
| `y` | float64 | 22.52 | Vertical position (**yards**, 0–53.33). |
| `s` | float64 | 0.28 | Instantaneous speed (**yd/s**). |
| `a` | float64 | 0.11 | Instantaneous acceleration (**yd/s²**). |
| `dis` | float64 | 0.03 | Distance from previous frame (**yards**). |
| `o` | float64 | 98.51 | Body **orientation** angle (degrees, 0–360). |
| `dir` | float64 | 126.08 | Motion **direction** angle (degrees, 0–360). |
| `event` | str / null | pass_forward | Play milestone event tag. |

### `event` Values (examples)

| Event | Description |
|-------|-------------|
| `ball_snap` | Ball is snapped |
| `pass_forward` | Forward pass thrown |
| `pass_arrived` | Pass reaches target |
| `first_contact` | First contact with ball carrier |
| `tackle` | Ball carrier tackled |
| `touchdown` | Touchdown scored |
| `out_of_bounds` | Player goes out of bounds |
| `null` | Regular tracking frame (most frames) |

> [!NOTE]
> **Key difference from Combine tracking:** Game tracking includes `o` (body orientation) and `event` columns, which Combine tracking does not have. Combine tracking has `entity_type`, `event_id`, `drill_type`, `drill_name`, and `attempt` columns that game tracking does not.
