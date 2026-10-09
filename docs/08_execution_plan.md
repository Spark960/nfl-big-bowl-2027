# 🎯 Execution Plan — "The Deceleration Advantage"

> **Objective:** Quantify Cornering Speed Retention (CSR) from Combine tracking data for DL pass rushers and prove it predicts NFL pass rush production better than traditional Combine metrics.
>
> **Deadline:** January 6, 2027 (11:59 PM UTC) — ~12 weeks from now
>
> **Deliverables:** (1) Public Kaggle Notebook, (2) ≤ 2,000 word markdown writeup with < 10 figures

---

## Phase 0: Project Setup *(Week 1, Days 1–2)*

### Checklist

- [x] **0.1** Set up project directory structure:
  ```
  nfl-kaggle-2026/
  ├── data/nfl-big-data-bowl-2027/   ← already have all 9 CSVs
  ├── docs/                          ← reference docs (already created)
  ├── notebooks/
  │   ├── 01_eda.ipynb
  │   ├── 02_combine_features.ipynb
  │   ├── 03_nfl_outcomes.ipynb
  │   ├── 04_analysis.ipynb
  │   └── 05_final_submission.ipynb  ← the public Kaggle notebook
  ├── src/
  │   ├── __init__.py
  │   ├── data_loading.py            ← reusable loaders with filters
  │   ├── combine_features.py        ← CSR, PDR, TRT, FSE computation
  │   ├── nfl_outcomes.py            ← pressure rate, get-off aggregation
  │   ├── visualization.py           ← all plot/animation functions
  │   └── utils.py                   ← coordinate math, angle helpers
  ├── outputs/
  │   ├── figures/
  │   └── tables/
  └── requirements.txt
  ```
- [x] **0.2** Create `requirements.txt` with core dependencies:
  - `pandas`, `numpy`, `scipy`, `scikit-learn`
  - `matplotlib`, `seaborn`, `plotly`
  - `statsmodels` (for regression diagnostics)
  - `tqdm` (progress bars for large file processing)
- [x] **0.3** Install dependencies in `.venv`
- [x] **0.4** Build `src/data_loading.py` with lazy-loading helpers that filter at read time to avoid OOM on the ~2 GiB game tracking files
- [x] **0.5** Verify all 9 data files load correctly with a quick sanity check (row counts match expected)

### Data References
| What | Where | Details |
|------|-------|---------|
| All 9 CSV files | `data/nfl-big-data-bowl-2027/` | [02_data_catalog.md](./02_data_catalog.md) — file sizes, row counts |
| Column definitions | — | [03_data_dictionary_combine.md](./03_data_dictionary_combine.md), [04_data_dictionary_nfl.md](./04_data_dictionary_nfl.md) |
| Coordinate system | — | [06_field_coordinate_system.md](./06_field_coordinate_system.md) — x/y/dir/o conventions |
| Competition rules | — | [01_competition_overview.md](./01_competition_overview.md) — word limits, judging criteria |
| Strategy & metric definitions | — | [07_winning_game_plan.md](./07_winning_game_plan.md) — full methodology |

---

## Phase 1: Exploratory Data Analysis *(Week 1–2)*

> **Goal:** Deeply understand the DL player data, drill structure, and frame-level tracking patterns before engineering any features.

### 1A — Identify Our Player Cohort

- [x] **1A.1** Load `players.csv` → filter to DL pass rushers: `nfl_position` in `['DE', 'OLB', 'DT', 'NT']`
  - Expected: ~118 players (66 edge + 52 interior)
  - **File:** `data/.../players.csv` — columns: `nfl_id`, `nfl_position`, `display_name`, `draft_year`, `draft_round`, `draft_overall_pick`
  - **Ref:** [03_data_dictionary_combine.md → File 1](./03_data_dictionary_combine.md)

- [x] **1A.2** Join with `combine_results.csv` on `nfl_id` → get their traditional Combine metrics
  - Key columns: `forty`, `ten_yd_split`, `three_cone`, `short_shuttle`, `vertical`, `broad_jump`, `ngs_athleticism_score`
  - Note which players have `null` for `three_cone` / `short_shuttle` (opt-outs)
  - **Ref:** [03_data_dictionary_combine.md → File 2](./03_data_dictionary_combine.md)

- [x] **1A.3** Check how many of these players also appear in `combine_tracking.csv` (verify `nfl_id` overlap)
  - Filter `combine_tracking.csv` to `drill_type` in `['SKILL_DRILLS_DL', 'THREE_CONE_DRILL', 'SHORT_SHUTTLE', 'FORTY_YARD_DASH']`
  - Count unique `nfl_id` values → expected: ~114 for SKILL_DRILLS_DL, 160 for 3-cone, etc.

- [x] **1A.4** Join with `player_career_successes.csv` on `nfl_id` → get career outcomes
  - Key columns: `career_defensive_snaps`, `career_games_started`, `career_games_active`, `ap_all_pro_1st_team`, `pro_bowl_original_ballot`
  - **Ref:** [04_data_dictionary_nfl.md → File 4](./04_data_dictionary_nfl.md)

- [x] **1A.5** Create a master roster DataFrame: one row per DL player with draft info + traditional Combine metrics + career outcomes. Save as `outputs/dl_roster_master.csv`

### 1B — Understand Combine Tracking Frame Structure

- [x] **1B.1** Load `combine_tracking.csv` filtered to DL-relevant `nfl_id`s
  - **File:** `data/.../combine_tracking.csv` (79.9 MiB, 463K rows total)
  - **Ref:** [03_data_dictionary_combine.md → File 3](./03_data_dictionary_combine.md)

- [x] **1B.2** Catalog every `drill_name` that DL players participate in:
  - Expected from EDA: `PASS_RUSH_DRILL`, `PASS_RUSH_DROP`, `RUN_AND_CLUB_DRILL`, `LINE_DRILL`, `FOUR_BAG_AGILITY_DRILL`, `BOX_DRILL`, `FRONT_START_WAVE_DRILL_AND_LATERAL_REACTION`, `RUN_THE_HOOP_DRILL`, `BODY_CONTROL_DRILL`
  - Plus shared drills: `FORTY_YARD_DASH`, `THREE_CONE_DRILL`, `SHORT_SHUTTLE`
  - For each drill: count frames, count unique players, count attempts

- [x] **1B.3** For 2–3 sample players, plot the **full trajectory** (x vs y) for each drill attempt — understand the drill's spatial shape
  - Use `event_id` to group frames within a single attempt
  - Color by `s` (speed) to see where they accelerate/decelerate
  - **Important:** Track `time` to verify 10 Hz sampling (frames should be ~0.10s apart)

- [x] **1B.4** For the same sample players, plot **speed profile** (`s` vs frame index) for each drill attempt
  - Identify the shape: does it look like a sprint (ramp up → plateau)? Or shuttle-like (ramp → brake → ramp)?
  - Mark frames where `dir` changes sharply (direction changes > 30°/frame)

- [x] **1B.5** For 3-cone and shuttle drills, plot **`dir` over time** to understand when direction changes happen
  - Identify the "turn frames" — these are where we'll compute CSR
  - Check: is the `dir` signal clean at 10 Hz? Or noisy? (determines smoothing needs)

- [x] **1B.6** Separate `entity_type == 'PLAYER'` vs `entity_type == 'BALL'` — understand if BALL data is useful for any DL drills
  - **Ref:** [03_data_dictionary_combine.md](./03_data_dictionary_combine.md) — `entity_type` description

- [x] **1B.7** Document findings: which drills have clear direction changes? Which are linear? Which have the most data per player? Write up in a short EDA summary. ([09_phase1_eda_summary.md](./09_phase1_eda_summary.md))

### 1C — Understand NFL Game Data Structure

- [x] **1C.1** Load `player_play.csv` filtered to our DL `nfl_id`s
  - **File:** `data/.../player_play.csv` (139.3 MiB, 316K rows total)
  - DL filter: `nfl_id` in our cohort AND `lined_up_position` in `['EDGE', 'INTERIOR_LINE', 'DE', 'DT', 'OLB', 'NT']` *(EDA discovery: `player_play.csv` uses `EDGE` and `INTERIOR_LINE`)*
  - **Ref:** [04_data_dictionary_nfl.md → File 5, Sections A + F](./04_data_dictionary_nfl.md)

- [x] **1C.2** Count pass rush snaps vs. run defense snaps per player
  - Pass rush snaps: plays where `player_get_off` is not null (indicates a pass rush)
  - Compute per-player: total pass rush snaps, total run snaps, pass rush ratio

- [x] **1C.3** Check availability of key defensive metrics per player:
  - `player_get_off` — expected ~67% of pass rush plays
  - `time_to_pressure` — expected ~6% (only when pressure occurred)
  - `sack` — binary per play
  - `quick_pressure` — binary per play
  - `tackle_for_loss` — binary per play
  - Determine minimum-snap threshold for reliable per-player aggregation (target: ≥ 50 pass rush snaps)

- [x] **1C.4** Peek at `game_tracking_2023.csv` for 1–2 specific pass rush plays by a known edge rusher
  - Load just those frames (filter by `game_id`, `play_id`, `nfl_id`)
  - Plot the x-y trajectory → visualize the rush path
  - Plot `s`, `a`, `dir`, `o` over time → understand the in-game movement signal
  - **File:** `data/.../game_tracking_2023.csv` (319.9 MiB)
  - **Ref:** [04_data_dictionary_nfl.md → Files 7–9](./04_data_dictionary_nfl.md)
  - **Ref:** [06_field_coordinate_system.md](./06_field_coordinate_system.md) — `o` vs `dir` meaning

- [x] **1C.5** Identify which `event` tags mark the relevant window for pass rush analysis
  - Start: `ball_snap`
  - End: `pass_forward`, `qb_sack`, `qb_scramble`, `tackle`, or `out_of_bounds`
  - Document the event sequence for a typical pass play

### Phase 1 Exit Criteria
> ✅ Master roster with draft + Combine + career data for ~114 DL players (`outputs/dl_roster_master.csv`, 118 players)  
> ✅ Clear understanding of which drills have usable direction-change data  
> ✅ Validated 10 Hz signal quality for both Combine and game tracking  
> ✅ Identified minimum-snap thresholds for NFL metric aggregation  
> ✅ EDA summary document with key findings and decisions ([`docs/09_phase1_eda_summary.md`](./09_phase1_eda_summary.md))

---

## Phase 2: Combine Feature Engineering *(Week 3–4)*

> **Goal:** Compute the 6 tracking-derived metrics from Combine data for every DL player.

### 2A — Signal Processing Utilities

- [x] **2A.1** Build `src/utils.py` — angle math helpers:
  - `angular_diff(a, b)` → shortest signed difference between two angles (handles 0/360 wrap)
  - `angular_rate(dir_series, dt=0.1)` → degrees/second of direction change
  - `smooth_series(series, window=3)` → rolling mean for noise reduction
  - **Ref:** [06_field_coordinate_system.md](./06_field_coordinate_system.md) — 0° = toward visitor endzone, clockwise

- [x] **2A.2** Build direction-change detection function:
  - Input: a single drill attempt's frames (sorted by `time`)
  - Compute `dir_change_rate = angular_rate(dir)` per frame
  - Identify "turn frames" where `abs(dir_change_rate) > threshold` (start with 30°/s, tune later)
  - Group consecutive turn frames into "turn events"
  - Return: list of turn events with start_frame, end_frame, total_angle_change

- [x] **2A.3** Validate on 5–10 known drill attempts (from Phase 1 EDA):
  - Plot trajectory with detected turns highlighted
  - Confirm turns align with visual direction changes
  - Tune threshold if needed

### 2B — Core Metric Computation

For each metric, implement in `src/combine_features.py`:

- [x] **2B.1** **Cornering Speed Retention (CSR)** — *headline metric*
  - For each detected turn event:
    - `entry_speed` = mean `s` in 3 frames before the turn (with pass-rush approach floor `4.8 yd/s`)
    - `min_speed` = min `s` during the turn
    - `csr_turn = min_speed / entry_speed`
  - Player CSR = median across all turns across all drill attempts
  - **Source data:** `combine_tracking.csv` → `s`, `dir` columns
  - **Drills:** `THREE_CONE_DRILL`, `SHORT_SHUTTLE`, and relevant SKILL_DRILLS_DL names (those with turns, identified in Phase 1)

- [x] **2B.2** **Peak Deceleration Rate (PDR)**
  - For each turn event:
    - Compute frame-to-frame speed change: `Δs = s[t] - s[t-1]`
    - PDR_turn = `min(Δs)` (most negative = hardest braking)
  - Player PDR = median across all turns
  - **Source data:** `combine_tracking.csv` → `s` column

- [x] **2B.3** **Turn Recovery Time (TRT)**
  - For each turn event:
    - Find the frame at `min(s)` during the turn
    - Count frames until `s` returns to `0.9 * entry_speed`
    - TRT_turn = frames × 0.1 seconds
  - Player TRT = median across all turns
  - **Source data:** `combine_tracking.csv` → `s` column

- [x] **2B.4** **First-Step Explosion (FSE)**
  - For each drill attempt:
    - Take frames 1–5 (first 0.5 seconds from movement onset)
    - FSE_attempt = `max(a)` in those frames
  - Player FSE = median across all attempts (across all DL drills)
  - **Source data:** `combine_tracking.csv` → `a` column
  - **Drills:** All SKILL_DRILLS_DL drills + FORTY_YARD_DASH

- [x] **2B.5** **Acceleration Curve Shape (ACS)**
  - From FORTY_YARD_DASH attempts (with fallback to sprint/skill drills for 40 opt-outs):
    - `early_accel` = mean `a` in frames 1–10 (first 1.0 seconds)
    - `late_accel` = mean `a` in frames 11–20 (1.0–2.0 seconds)
    - ACS = `early_accel / late_accel` (higher = more front-loaded explosion)
  - Player ACS = median across attempts
  - **Source data:** `combine_tracking.csv` → `a` column, filtered to `drill_type == 'FORTY_YARD_DASH'`

- [x] **2B.6** **Directional Jerk (DJ)** — movement smoothness
  - For each turn event:
    - Compute second derivative of `dir` (rate of change of direction-change-rate)
    - DJ_turn = std deviation of the second derivative (lower = smoother)
  - Player DJ = median across all turns
  - **Source data:** `combine_tracking.csv` → `dir` column

### 2C — Assemble & Validate Combine Features

- [x] **2C.1** Compute all 6 metrics for every DL player → output a DataFrame: one row per player, columns = `[nfl_id, CSR, PDR, TRT, FSE, ACS, DJ]`

- [x] **2C.2** Quality checks:
  - No infinite / NaN values (handle edge cases: players with zero turns detected)
  - Distributions look reasonable (histogram each metric)
  - Correlation matrix between the 6 tracking metrics — are they measuring different things?
  - Correlation of tracking metrics with traditional metrics (3-cone, shuttle, 40) — they should correlate but NOT be redundant

- [x] **2C.3** Merge with traditional Combine metrics (from `combine_results.csv`) to create a full Combine feature matrix
  - Columns: `nfl_id`, `forty`, `ten_yd_split`, `three_cone`, `short_shuttle`, `vertical`, `broad_jump`, `ngs_athleticism_score`, `CSR`, `PDR`, `TRT`, `FSE`, `ACS`, `DJ`

- [x] **2C.4** Save as `outputs/dl_combine_features.csv`

### Phase 2 Exit Criteria
> ✅ 6 tracking-derived metrics computed for ~114 DL players  
> ✅ Metrics pass quality checks (no NaN, reasonable distributions)  
> ✅ CSR and traditional 3-cone show correlation ~0.3–0.6 (related but not redundant)  
> ✅ Feature matrix saved and ready for modeling

---

## Phase 3: NFL Outcome Engineering *(Week 5–6)*

> **Goal:** Compute per-player NFL performance metrics that we'll predict from Combine features.

### 3A — Aggregate Play-Level Metrics

- [ ] **3A.1** Load `player_play.csv` filtered to our DL `nfl_id` cohort
  - **File:** `data/.../player_play.csv` → 316K rows total, filter to ~118 DL players
  - **Ref:** [04_data_dictionary_nfl.md → File 5, Section F](./04_data_dictionary_nfl.md)

- [ ] **3A.2** Classify each play as **pass rush** or **run defense**:
  - Pass rush: `player_get_off` is not null
  - Alternative: `blitzing` is not null, or `sack` is not null
  - Document the classification logic

- [ ] **3A.3** Compute per-player aggregates (pass rush plays only):

  | Metric | Formula | Column Source |
  |--------|---------|---------------|
  | `pressure_rate` | count(`time_to_pressure` not null) / count(pass rush plays) | `time_to_pressure` |
  | `quick_pressure_rate` | sum(`quick_pressure`) / count(pass rush plays) | `quick_pressure` |
  | `avg_get_off` | mean(`player_get_off`) | `player_get_off` |
  | `sack_rate` | sum(`sack`) / count(pass rush plays) | `sack` |
  | `tfl_rate` | sum(`tackle_for_loss`) / count(all defensive plays) | `tackle_for_loss` |
  | `total_pass_rush_snaps` | count(pass rush plays) | — |
  | `total_defensive_snaps` | count(all plays for player) | — |

- [ ] **3A.4** Apply minimum snap threshold — exclude players with < 50 pass rush snaps (unreliable rates)
  - Document how many players are excluded (likely 2025 draft class rookies with few snaps)
  - Note: this is a **sensitivity analysis** decision — we'll test 30, 50, 75 thresholds later

- [ ] **3A.5** Merge with `player_career_successes.csv` to add:
  - `snap_share` = `career_defensive_snaps` / `career_games_active`
  - `start_rate` = `career_games_started` / `career_games_active`
  - `accolades` = `ap_all_pro_1st_team` + `ap_all_pro_2nd_team` + `pro_bowl_original_ballot`
  - **Ref:** [04_data_dictionary_nfl.md → File 4](./04_data_dictionary_nfl.md)

- [ ] **3A.6** Save as `outputs/dl_nfl_outcomes.csv`

### 3B — Game Tracking Rush Paths (for validation & visuals)

- [ ] **3B.1** For each DL player, identify their **top 5 pass rush plays** (lowest `time_to_pressure` or plays with a sack)
  - Pull `game_id` + `play_id` combos from `player_play.csv`

- [ ] **3B.2** Load those specific plays from `game_tracking_*.csv`
  - **Strategy:** Don't load entire files. Use `pandas` chunked reading or `dask` to filter by `game_id` + `play_id` + `nfl_id`
  - **Files:** `data/.../game_tracking_2023.csv` (320 MiB), `game_tracking_2024.csv` (685 MiB), `game_tracking_2025.csv` (975 MiB)
  - **Ref:** [04_data_dictionary_nfl.md → Files 7–9](./04_data_dictionary_nfl.md)

- [ ] **3B.3** Extract frames between `ball_snap` and `pass_forward`/`qb_sack` events
  - Compute **in-game CSR** using the same algorithm from Phase 2 on rush path direction changes
  - This validates whether Combine CSR translates to game movement

- [ ] **3B.4** Save extracted rush paths as `outputs/dl_game_rush_paths.pkl` (for visualization in Phase 5)

### Phase 3 Exit Criteria
> ✅ Per-player NFL outcome metrics for ~80–100 DL players (post minimum-snap filter)  
> ✅ Outcome distributions checked (no outlier issues, reasonable ranges)  
> ✅ In-game CSR computed for a subset of players (for Combine→Game validation)  
> ✅ Rush path frames saved for case study visualizations

---

## Phase 4: Statistical Analysis *(Week 7–8)*

> **Goal:** Prove that tracking-derived metrics (especially CSR) predict NFL outcomes better than traditional Combine metrics.

### 4A — Correlation & Exploration

- [ ] **4A.1** Merge `dl_combine_features.csv` with `dl_nfl_outcomes.csv` on `nfl_id`
  - This is the **master analysis DataFrame** — one row per player, all features + outcomes

- [ ] **4A.2** Compute full correlation matrix: all 6 tracking metrics × all NFL outcome metrics
  - Highlight strongest correlations
  - Identify which tracking metric has the strongest individual correlation with `pressure_rate`

- [ ] **4A.3** Scatter plot matrix: CSR vs. each NFL outcome metric
  - Add draft round as color/marker to identify if high CSR + low draft round = hidden gem

- [ ] **4A.4** Compare tracking metrics vs. traditional metrics head-to-head:
  - Correlation of `CSR` with `pressure_rate` vs. correlation of `three_cone` with `pressure_rate`
  - If CSR wins → that's our headline finding
  - If it's close → show CSR adds incremental value (partial correlation controlling for 3-cone)

### 4B — The Key Regression Test

- [ ] **4B.1** **Model A (Baseline):** OLS regression predicting `pressure_rate` from traditional metrics only
  - Predictors: `three_cone`, `short_shuttle`, `forty`, `ngs_athleticism_score`
  - Handle missing values (some players opted out of 3-cone/shuttle) — either impute or restrict sample
  - Record: R², adjusted R², AIC, BIC, cross-validated RMSE (leave-one-out due to small N)

- [ ] **4B.2** **Model B (Tracking-enhanced):** OLS regression adding tracking metrics
  - Predictors: same as A + `CSR`, `PDR`, `TRT`, `FSE`
  - Record: R², adjusted R², AIC, BIC, cross-validated RMSE
  - **THE KEY COMPARISON:** Does Model B significantly improve over Model A?
  - Use F-test for nested model comparison or likelihood ratio test

- [ ] **4B.3** **Model C (Tracking-only):** OLS regression with only tracking metrics
  - Predictors: `CSR`, `PDR`, `TRT`, `FSE`, `ACS`, `DJ`
  - If this beats Model A → strongest possible finding ("tracking alone > traditional")
  - If not → "tracking adds value on top of traditional" is still a strong finding

- [ ] **4B.4** Repeat 4B.1–4B.3 for secondary outcomes:
  - `avg_get_off` (process metric — direct parallel to FSE)
  - `sack_rate` (high-value outcome)
  - `snap_share` (career outcome)

- [ ] **4B.5** Sensitivity analyses:
  - Vary minimum snap threshold (30, 50, 75) — do results hold?
  - Separate by draft year (do 2023 prospects with 3 years of data show stronger signal?)
  - Check for position sub-group differences (edge vs. interior)

### 4C — Combine-to-Game Movement Validation

- [ ] **4C.1** Correlate Combine CSR with in-game CSR (computed in Phase 3B.3)
  - Scatter plot: `Combine CSR` vs `In-Game CSR`
  - If significantly correlated → proves the trait transfers from drill to game
  - This is the **"translation chain"** evidence the judges want

- [ ] **4C.2** Test: Does Combine CSR predict in-game CSR, which then predicts pressure rate?
  - This is a mediation analysis: Combine CSR → Game CSR → NFL outcomes
  - Even a simple two-step correlation is compelling

### Phase 4 Exit Criteria
> ✅ Model comparison table showing Model B > Model A (tracking adds value)  
> ✅ CSR has significant correlation with pressure_rate (or sack_rate or avg_get_off)  
> ✅ Combine CSR correlates with in-game CSR (trait transfers)  
> ✅ Results robust across sensitivity analyses  
> ✅ Statistical tables and key numbers documented

---

## Phase 5: Visualization & Case Studies *(Week 9–10)*

> **Goal:** Create the < 10 figures and identify 2–3 compelling player case studies.

### 5A — Figure Production

Build all figures in `src/visualization.py`, render to `outputs/figures/`.

- [ ] **5A.1** **Figure 1 — "The Hook" (Acceleration Curve Comparison)**
  - Two DL players with nearly identical 3-cone times but different CSR scores
  - Plot speed vs. time during the 3-cone drill for both players
  - Annotate: "Same drill time. Different movement quality."
  - **Data source:** `combine_tracking.csv` filtered to specific `event_id`s

- [ ] **5A.2** **Figure 2 — CSR Distribution by NFL Outcome Tier**
  - Violin/box plot: group DL players into tiers by `pressure_rate` (top quartile, middle, bottom)
  - Show CSR distribution for each tier
  - **Data source:** merged analysis DataFrame from Phase 4

- [ ] **5A.3** **Figure 3 — Model Comparison Table**
  - Clean formatted table: Model A vs. B vs. C
  - Columns: Predictors, R², Adj R², CV-RMSE, ΔR² from baseline
  - Highlight Model B improvement in bold or color
  - **Data source:** Phase 4B results

- [ ] **5A.4** **Figure 4 — Scatter: CSR vs. NFL Pressure Rate**
  - Each point = one DL player
  - Color by draft round (1st round = gold, 2–3 = blue, 4+ = gray, UDFA = red)
  - Add regression line with confidence interval
  - Label notable players (hidden gems and busts)
  - **Data source:** merged analysis DataFrame

- [ ] **5A.5** **Figure 5 — Combine Drill Path Comparison**
  - Side-by-side x-y trajectory plots for a high-CSR and low-CSR player on the same drill
  - Color path by speed (blue = slow, red = fast)
  - Show how the high-CSR player maintains speed (stays red) through turns
  - **Data source:** `combine_tracking.csv` specific `event_id`s

- [ ] **5A.6** **Figure 6 — Game Rush Path Comparison**
  - Same two players from Fig 5, now showing an actual NFL pass rush path
  - x-y trajectory from `ball_snap` to `pass_forward`
  - Color by speed, same scale as Fig 5
  - Shows the trait carrying from drill to game
  - **Data source:** `game_tracking_*.csv` specific plays from Phase 3B

- [ ] **5A.7** **Figure 7 — Player Case Study Cards (2–3 players)**
  - Infographic-style cards showing:
    - Player name, draft position, photo placeholder
    - Traditional metrics (40, 3-cone) vs. tracking metrics (CSR, FSE)
    - NFL outcomes (pressure rate, sack count, snap share)
    - One-line verdict: "Hidden Gem — CSR identified what the stopwatch missed"
  - **Data source:** all merged data

- [ ] **5A.8** **Figure 8 — Feature Importance**
  - Bar chart: which features predict NFL pressure rate?
  - Show both traditional and tracking features
  - Highlight CSR's ranking
  - Method: standardized regression coefficients or permutation importance from a random forest
  - **Data source:** Phase 4B model outputs

### 5B — Case Study Selection

- [ ] **5B.1** Identify **"Hidden Gems"**: players with below-average traditional metrics but **high CSR** who succeeded in the NFL
  - Filter: `three_cone > median` AND `CSR > 75th percentile` AND `pressure_rate > median`
  - These are the "CSR would have told you" stories

- [ ] **5B.2** Identify **"Red Flags"**: highly drafted players with **low CSR** who underperformed
  - Filter: `draft_round <= 2` AND `CSR < 25th percentile` AND `pressure_rate < median`
  - These are the "CSR would have warned you" stories

- [ ] **5B.3** Select 2–3 most compelling case studies, verify their narrative holds up (check for injuries, position changes, or other confounders by searching player history)

### Phase 5 Exit Criteria
> ✅ All 8 figures produced and polished  
> ✅ 2–3 case studies selected with compelling narratives  
> ✅ Figures are clear, properly labeled, and publication-ready  
> ✅ Total figure count ≤ 10 (including any tables)

---

## Phase 6: Writeup *(Week 11)*

> **Goal:** Draft the ≤ 2,000 word markdown submission.

### 6A — Writing

- [ ] **6A.1** Draft Section 1: **The Problem** (~200 words)
  - The Combine stopwatch tells you HOW FAST, tracking data tells you HOW
  - Set up the question: what does the stopwatch miss?

- [ ] **6A.2** Draft Section 2: **The Metric** (~300 words)
  - Introduce Cornering Speed Retention (CSR)
  - Explain with Figure 1 (two players, same 3-cone, different CSR)
  - Intuitive explanation: "how much speed you keep through direction changes"

- [ ] **6A.3** Draft Section 3: **The Evidence** (~400 words)
  - Model comparison (Figure 3)
  - CSR vs. pressure rate scatter (Figure 4)
  - Key statistical results in plain language

- [ ] **6A.4** Draft Section 4: **The Translation** (~400 words)
  - Combine CSR → in-game CSR correlation
  - Drill path vs. rush path visuals (Figures 5 & 6)
  - "The trait transfers from Indianapolis to Sunday"

- [ ] **6A.5** Draft Section 5: **Case Studies** (~400 words)
  - 2–3 player profiles (Figure 7)
  - "Player A: overlooked by the stopwatch, revealed by tracking"

- [ ] **6A.6** Draft Section 6: **For the Draft Room** (~300 words)
  - Actionable recommendations
  - Feature importance chart (Figure 8)
  - "When evaluating DL prospects, compute CSR. Prospects above X threshold are Y times more likely to..."

- [ ] **6A.7** Word count check — must be ≤ 2,000. Cut ruthlessly if over.
  - **Ref:** [01_competition_overview.md](./01_competition_overview.md) — submission requirements

### 6B — Review

- [ ] **6B.1** Read aloud — does it flow? Is the narrative compelling?
- [ ] **6B.2** Check all figures are embedded and numbered correctly
- [ ] **6B.3** Verify all statistical claims match the actual numbers
- [ ] **6B.4** Ensure code appendix / linked notebook reference is included
- [ ] **6B.5** Proofread for typos, unclear sentences, jargon

### Phase 6 Exit Criteria
> ✅ Complete markdown writeup, ≤ 2,000 words  
> ✅ All 8 figures embedded  
> ✅ Narrative is compelling and accessible to a non-data-scientist  
> ✅ All statistical claims verified

---

## Phase 7: Polish & Submit *(Week 12)*

> **Goal:** Finalize the public Kaggle Notebook and submit.

- [ ] **7.1** Create `05_final_submission.ipynb` — clean, annotated Kaggle Notebook
  - All code cells run top-to-bottom without error
  - Clear markdown headings between sections
  - Output cells show key figures and tables
  - Remove debug/scratch code

- [ ] **7.2** Verify notebook runs on Kaggle's infrastructure:
  - Upload as a Kaggle Notebook linked to the competition dataset
  - Run it end-to-end on Kaggle's servers
  - Fix any path issues (Kaggle paths: `/kaggle/input/nfl-big-data-bowl-2027/`)

- [ ] **7.3** Make the notebook **Public** on Kaggle

- [ ] **7.4** Final submission checklist:
  - [ ] Writeup ≤ 2,000 words ✓
  - [ ] < 10 tables/figures ✓
  - [ ] Uses player tracking data ✓
  - [ ] Explicitly links Combine tracking → NFL game performance ✓
  - [ ] Readable markdown with embedded visuals ✓
  - [ ] Public Kaggle Notebook attached ✓
  - [ ] Code in appendix/notebook (not cluttering writeup) ✓
  - **Ref:** [01_competition_overview.md](./01_competition_overview.md) — full submission requirements

- [ ] **7.5** Submit before **January 6, 2027, 11:59 PM UTC**

---

## Quick Reference: Where Is Everything?

| Need | File | Relevant Doc |
|------|------|-------------|
| Player roster + draft info | `data/.../players.csv` | [03_data_dictionary_combine.md → File 1](./03_data_dictionary_combine.md) |
| Traditional Combine metrics | `data/.../combine_results.csv` | [03_data_dictionary_combine.md → File 2](./03_data_dictionary_combine.md) |
| 10 Hz Combine drill tracking | `data/.../combine_tracking.csv` | [03_data_dictionary_combine.md → File 3](./03_data_dictionary_combine.md) |
| Career outcomes & accolades | `data/.../player_career_successes.csv` | [04_data_dictionary_nfl.md → File 4](./04_data_dictionary_nfl.md) |
| Per-play NFL metrics (64 cols) | `data/.../player_play.csv` | [04_data_dictionary_nfl.md → File 5](./04_data_dictionary_nfl.md) |
| Game schedule metadata | `data/.../games.csv` | [04_data_dictionary_nfl.md → File 6](./04_data_dictionary_nfl.md) |
| In-game 10 Hz tracking | `data/.../game_tracking_*.csv` | [04_data_dictionary_nfl.md → Files 7–9](./04_data_dictionary_nfl.md) |
| Coordinate system + angles | — | [06_field_coordinate_system.md](./06_field_coordinate_system.md) |
| Competition rules & deadlines | — | [01_competition_overview.md](./01_competition_overview.md) |
| Full strategy & metric defs | — | [07_winning_game_plan.md](./07_winning_game_plan.md) |
| Data file sizes & ERD | — | [02_data_catalog.md](./02_data_catalog.md) |
