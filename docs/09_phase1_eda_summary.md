# Phase 1 Exploratory Data Analysis (EDA) Summary

> **Status:** Complete  
> **Generated Outputs:**
> - Master DL Roster: [`outputs/dl_roster_master.csv`](../outputs/dl_roster_master.csv) (`118` players × `38` columns)
> - Combine Drill Catalog: [`outputs/tables/dl_drill_catalog.csv`](../outputs/tables/dl_drill_catalog.csv)
> - NFL Snap & Metric Summary: [`outputs/tables/dl_snap_summary.csv`](../outputs/tables/dl_snap_summary.csv)
> - Figures:
>   - [`outputs/figures/phase1b_sample_trajectories.png`](../outputs/figures/phase1b_sample_trajectories.png)
>   - [`outputs/figures/phase1b_speed_profiles.png`](../outputs/figures/phase1b_speed_profiles.png)
>   - [`outputs/figures/phase1b_dir_over_time.png`](../outputs/figures/phase1b_dir_over_time.png)
>   - [`outputs/figures/phase1c_game_rush_samples.png`](../outputs/figures/phase1c_game_rush_samples.png)

---

## 0. Data File Sanity Check (Phase 0.5)

All 9 competition CSV files were verified in `data/nfl-big-data-bowl-2027/`:

| File | Exact Rows | Columns | Notes |
|------|-----------:|--------:|-------|
| `players.csv` | 510 | 10 | 510 rookie prospects (2023–2025 draft classes) |
| `combine_results.csv` | 510 | 18 | 1:1 join with `players.csv` on `nfl_id` |
| `combine_tracking.csv` | 463,189 | 14 | 10 Hz Combine drill tracking (`PLAYER` and `BALL`) |
| `player_career_successes.csv` | 510 | 9 | 1:1 join with `players.csv` on `nfl_id` |
| `player_play.csv` | 327,019 | 64 | Per-play NFL metrics across 2023–2025 |
| `games.csv` | 1,002 | 7 | Game schedule metadata (2023–2025) |
| `game_tracking_2023.csv` | 3,665,443 | 12 | 10 Hz in-game tracking (2023 season) |
| `game_tracking_2024.csv` | 7,827,944 | 12 | 10 Hz in-game tracking (2024 season) |
| `game_tracking_2025.csv` | 11,160,903 | 12 | 10 Hz in-game tracking (2025 season) |

---

## 1A. DL Pass Rusher Cohort & Traditional Combine Opt-Outs

1. **Cohort Size (`1A.1`):**
   - Filtering `players.csv` to `nfl_position in ['DE', 'OLB', 'DT', 'NT']` yields **118 DL prospects**:
     - **66 Edge rushers:** `36 DE` + `30 OLB`
     - **52 Interior linemen:** `47 DT` + `5 NT`

2. **Traditional Combine Stopwatch Availability (`1A.2`):**
   - `ngs_athleticism_score`: **118 / 118** (0.0% missing)
   - `vertical`: **102 / 118** (13.6% opt-out)
   - `broad_jump`: **97 / 118** (17.8% opt-out)
   - `forty` & `ten_yd_split`: **94 / 118** (20.3% opt-out)
   - `short_shuttle`: **46 / 118** (**61.0% opt-out**)
   - `three_cone`: **43 / 118** (**63.6% opt-out**)

3. **Combine Tracking Overlap (`1A.3`):**
   - **118 / 118 (100%)** of our DL cohort appear in `combine_tracking.csv`:
     - `SKILL_DRILLS_DL`: **114** DL players (all 114 participants in the dataset; the remaining 4 `OLB` players ran `SKILL_DRILLS_LB`)
     - `FORTY_YARD_DASH`: **93** DL players (418 across all positions)
     - `THREE_CONE_DRILL`: **45** DL players (160 across all positions)
     - `SHORT_SHUTTLE`: **38** DL players (170 across all positions)
   - **Strategic Implication:** Over 60% of DL prospects skip the 3-cone and short shuttle stopwatch drills, leaving scouts blind on traditional agility times. However, **96.6% (114/118)** run the on-field `SKILL_DRILLS_DL` tracking drills (and 100% run either `SKILL_DRILLS_DL` or `SKILL_DRILLS_LB`), allowing us to compute tracking-derived Cornering Speed Retention (CSR) for virtually the entire cohort.

4. **Career Outcomes (`1A.4`–`1A.5`):**
   - Merged `players.csv` + `combine_results.csv` + tracking flags + `player_career_successes.csv` into [`outputs/dl_roster_master.csv`](../outputs/dl_roster_master.csv) (`118` rows, `38` columns).
   - Across the cohort, average career volume is **445.8 defensive snaps** and **5.7 games started**.

---

## 1B. Combine Tracking Frame Structure & Signal Quality

1. **10 Hz Sampling & Signal Cleanliness (`1B.3`, `1B.5`):**
   - Across all `97,124` DL tracking frames (`1,325` drill attempts), **100.00%** of within-attempt frame intervals are exactly `dt = 0.100s` (10 Hz).
   - Both `s` (speed) and `dir` (direction of motion) are remarkably clean during active movement (`s > 0.5 yd/s`), with smooth acceleration/deceleration profiles and clear angular transitions once `0°/360°` wraparound is handled via shortest signed angular difference. Minimal smoothing (`window=3` or none) is needed inside active drill windows.

2. **`PLAYER` vs. `BALL` Entities (`1B.6`):**
   - Across the entire `combine_tracking.csv` file, `entity_type == 'BALL'` only exists in `SKILL_DRILLS_WR` (`23,975` frames) and `SKILL_DRILLS_TE` (`8,120` frames).
   - There are **0 `BALL` frames** in `SKILL_DRILLS_DL`, `SKILL_DRILLS_LB`, `THREE_CONE_DRILL`, `SHORT_SHUTTLE`, or `FORTY_YARD_DASH`. Filtering to `entity_type == 'PLAYER'` retains 100% of DL tracking data.

3. **DL Drill Catalog & Classification (`1B.2`, `1B.7`):**

| Drill Type | Drill Name | Players | Attempts | Avg Frames | Avg Max Speed (yd/s) | Avg Active Frames `\|Δdir\| > 15°` | Avg Active Frames `\|Δdir\| > 30°` | Movement Profile & Phase 2 Usage |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `FORTY_YARD_DASH` | `FORTY_YARD_DASH` | 93 | 177 | 53.2 | 10.01 | 0.22 | 0.03 | **Linear sprint** (sinuosity `1.00`) → Use for **FSE** & **ACS** |
| `THREE_CONE_DRILL` | `THREE_CONE_DRILL` | 45 | 60 | 78.6 | 6.27 | 9.00 | 5.25 | **Sharp cuts + L-bend cornering** → Primary **CSR / PDR / TRT / DJ** |
| `SHORT_SHUTTLE` | `SHORT_SHUTTLE` | 38 | 44 | 52.2 | 5.74 | 4.61 | 3.11 | **Two 180° plant-and-return cuts** → Primary **PDR / TRT / CSR** |
| `SKILL_DRILLS_DL` | `FRONT_START_WAVE_DRILL_AND_LATERAL_REACTION` | 112 | 112 | 114.7 | 7.68 | 9.37 | 4.89 | **Multi-directional lateral/forward cuts** → Use for **CSR / PDR / TRT** |
| `SKILL_DRILLS_DL` | `FOUR_BAG_AGILITY_DRILL` | 112 | 112 | 104.5 | 7.15 | 10.44 | 2.97 | **4-bag weaving agility cuts + sprint finish** → Use for **CSR / PDR / TRT** |
| `SKILL_DRILLS_DL` | `PASS_RUSH_DRILL` | 114 | 217 | 45.4 | 7.61 | 0.98 | 0.08 | **Explosive get-off + ~90° edge cornering arc** → Use for **FSE** & **Curved CSR** |
| `SKILL_DRILLS_DL` | `RUN_THE_HOOP_DRILL` | 109 | 119 | 76.6 | 6.42 | 2.45 | 0.11 | **Continuous figure-8 hoop bend at speed** → Use for **Curved CSR** |
| `SKILL_DRILLS_DL` | `RUN_AND_CLUB_DRILL` | 112 | 113 | 72.4 | 5.60 | 4.73 | 0.80 | **Pass rush club move + redirect** → Use for **CSR / FSE** |
| `SKILL_DRILLS_DL` | `BODY_CONTROL_DRILL` | 111 | 113 | 58.5 | 8.15 | 2.93 | 0.36 | **Explosive burst + bend/redirect** → Use for **CSR / FSE** |
| `SKILL_DRILLS_DL` | `BACK_PEDAL_AND_REACT` | 55 | 58 | 104.4 | 7.12 | 2.88 | 1.29 | **Backpedal + 180° break** (mostly edge/hybrid) → Secondary agility |
| `SKILL_DRILLS_DL` | `SHORT_ZONE_BREAKS` (4 variants) | 36 | 163 | ~80.0 | ~7.60 | ~2.30 | ~0.50 | **Drop-into-zone breaks** (edge rushers) → Secondary agility |

4. **Critical Insight for Phase 2 Turn Detection (`1B.4`–`1B.5`):**
   - Note the unit distinction in `08_execution_plan.md`: `30°/s` at 10 Hz (`dt = 0.1s`) is **`3°/frame`**, whereas `30°/frame` is **`300°/s`**.
   - **Hard 180° plant cuts** (`SHORT_SHUTTLE`, Cone 1 touch in `THREE_CONE_DRILL`, bag plants in `FOUR_BAG_AGILITY_DRILL`) reach `|Δdir| > 30°/frame` (`> 300°/s`) and drop speed near `0.2–0.8 yd/s`.
   - **High-speed cornering arcs** (the L-bend around Cones 2 & 3 in `THREE_CONE_DRILL`, figure-8 arcs in `RUN_THE_HOOP_DRILL`, and the edge bend in `PASS_RUSH_DRILL`) sustain `|Δdir| ≈ 10°–25°/frame` (`100°–250°/s`) over 4–8 consecutive frames (cumulative turn `45°–180°`) while maintaining `s ≈ 1.5–6.0 yd/s`.
   - **Decision for Phase 2A:** Detect turn events inside the active drill window (`s > 0.5 yd/s` start-to-finish) using an angular rate threshold of **`100°/s` (`10°/frame`)** grouped across consecutive turning frames with a minimum total angle change of **`45°`**. This cleanly captures both sharp agility cuts and continuous pass-rush cornering bends.

---

## 1C. NFL Game Data Structure & Snap Thresholds

1. **Critical Position Schema Discovery (`1C.1`):**
   - While `players.csv` codes DL positions as `['DE', 'OLB', 'DT', 'NT']`, **`player_play.csv` codes `lined_up_position` as `'EDGE'` (`36,831` plays) and `'INTERIOR_LINE'` (`30,172` plays)** (plus `73` `'OLB'` plays).
   - Filtering `lined_up_position` strictly to `['DE', 'DT', 'OLB', 'NT']` would drop `99.9%` of DL snaps (`67,003` plays).
   - We updated `DL_LINED_UP_POSITIONS = ['EDGE', 'INTERIOR_LINE', 'DE', 'DT', 'OLB', 'NT']` in `src/data_loading.py`, capturing all **67,076 DL snaps** across **115 players** (3 late-round/UDFA prospects have 0 NFL snaps).

2. **Pass Rush vs. Run Defense Split (`1C.2`):**
   - Out of `67,076` DL snaps:
     - **43,167 (`64.4%`)** are **pass rush snaps** (`player_get_off` is non-null).
     - **23,909 (`35.6%`)** are **run defense / coverage snaps**.

3. **Defensive Metric Availability on Pass Rush Snaps (`1C.3`):**
   - `player_get_off`: **43,167 / 43,167 (`100.0%` of pass rush snaps, `64.4%` of all DL snaps)**
   - `time_to_pressure`: **3,376 / 43,167 (`7.82%` of pass rush snaps)** → directly defines play-level pressure
   - `time_to_qb_hurry`: **3,446 / 43,167 (`7.98%` of pass rush snaps)**
   - `quick_pressure` (`== 1.0`): **1,013 / 43,167 (`2.35%` of pass rush snaps)**
   - `sack` (`> 0`): **493 / 43,167 (`1.14%` of pass rush snaps)** (`32,783` non-null `0.0/0.5/1.0` records)
   - `tackle_for_loss` (`> 0`): **700 / 67,076 (`1.04%` of all DL snaps)**

4. **Minimum Pass Rush Snap Threshold Analysis (`1C.3`):**
   - **>= 1 pass rush snap:** `115 / 118` players (`2023: 36, 2024: 36, 2025: 43`)
   - **>= 30 pass rush snaps:** `112 / 118` players (`2023: 35, 2024: 36, 2025: 41`)
   - **>= 50 pass rush snaps (Target Primary Threshold):** **`103 / 118` players** (`2023: 34, 2024: 33, 2025: 36`)
   - **>= 75 pass rush snaps:** `94 / 118` players (`2023: 33, 2024: 29, 2025: 32`)
   - **>= 100 pass rush snaps:** `85 / 118` players (`2023: 32, 2024: 27, 2025: 26`)
   - **Decision:** The target threshold of **≥ 50 pass rush snaps** retains **103 of 118 (`87.3%`)** DL players with balanced representation across all three draft classes (`34`, `33`, `36`), providing a strong sample size for Phase 3–4 modeling while sensitivity-testing `30` (`n=112`) and `75` (`n=94`).

5. **In-Game 10 Hz Tracking & Pass Rush Event Window (`1C.4`–`1C.5`):**
   - Verified 10 Hz sampling (`median dt = 0.100s`) and clean `x, y, s, a, dir, o` signals on sample 2023 pass rush plays (e.g., Will Anderson strip-sack in `game_id=2023081952, play_id=918`; YaYa Diaby sack in `game_id=2023111908, play_id=1234`).
   - **Pass Rush Event Window:**
     - **Start event:** `ball_snap` (typically `0.9–1.0s` into play tracking, after pre-snap events like `line_set`, `shift`, `man_in_motion`).
     - **End event:** First occurrence of `pass_forward`, `qb_sack`, `qb_strip_sack`, `pass_shovel`, `qb_spike`, `qb_kneel`, `run`, `handoff`, `tackle`, or `out_of_bounds` (typically `2.0–4.0s` after `ball_snap`).
