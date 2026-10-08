# Data Dictionary — Combine Side

Covers: `players.csv`, `combine_results.csv`, `combine_tracking.csv`

---

## File 1: `players.csv`

Demographic, collegiate, and draft metadata for 510 rookie prospects.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `nfl_id` | int64 | 55867 | **Primary key.** Unique NFL player identifier across all tables. |
| `display_name` | str | Will Anderson | Player's full legal name. |
| `draft_year` | int64 | 2023 | Year entered the NFL Draft (2023, 2024, 2025). |
| `nfl_position` | str | DE | Official roster position (WR, CB, T, G, C, DT, DE, OLB, TE, SS, FS, NT, DB, ILB, MLB, RB, FB). |
| `birth_date` | str | 2001-09-02 | Date of birth (YYYY-MM-DD). |
| `college_name` | str | Alabama | College/university. |
| `college_conference` | str | Southeastern Conference | NCAA conference. |
| `draft_round` | int64 / null | 1 | Draft round (1–7). `null` for UDFAs. |
| `draft_pick_within_round` | int64 / null | 3 | Pick within round. `null` for UDFAs. |
| `draft_overall_pick` | int64 / null | 3 | Overall pick (1–259+). `null` for UDFAs. |

---

## File 2: `combine_results.csv`

Official anthropometrics, physical testing splits, and NGS draft grades.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `draft_year` | int64 | 2023 | Combine year (2023, 2024, 2025). |
| `nfl_id` | int64 | 56040 | Player identifier → `players.csv`. |
| `combine_position` | str | TE | Position group at Combine drills. |
| `combine_height` | float64 | 77.875 | Height in **inches** (77.875 = 6'5.875"). |
| `combine_weight` | int64 | 245 | Weight in **pounds**. |
| `hand_size` | float64 | 10.0 | Hand span (thumb tip to pinky tip) in inches. |
| `arm_length` | float64 | 32.25 | Arm length (acromion to middle fingertip) in inches. |
| `wing_span` | float64 | 79.75 | Total fingertip-to-fingertip wingspan in inches. |
| `ten_yd_split` | float64 | 1.60 | 10-yard split time during 40-yard dash (**seconds**). |
| `forty` | float64 | 4.84 | 40-yard dash time (**seconds**). |
| `vertical` | float64 | 38.5 | Standing vertical jump (**inches**). |
| `broad_jump` | float64 | 125.0 | Standing broad jump (**inches**). |
| `three_cone` | float64 / null | 7.12 | 3-cone (L-drill) time (**seconds**). `null` = opt-out. |
| `short_shuttle` | float64 / null | 4.25 | 20-yard short shuttle (5-10-5) time (**seconds**). `null` = opt-out. |
| `bench_reps` | float64 / null | 22.0 | 225 lb bench press reps. `null` = opt-out. |
| `ngs_athleticism_score` | int64 | 60 | NGS composite athleticism score (0–100 percentile). |
| `ngs_college_production_score` | float64 | 78.2 | NGS college production score. |
| `ngs_final_score` | float64 | 74.5 | NGS overall prospect score (athleticism + production). |

---

## File 3: `combine_tracking.csv`

10 Hz optical sensor tracking for 6,310 Combine drill attempts.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `draft_year` | int64 | 2025 | Combine year. |
| `event_id` | str | 2025030210... | **Unique drill attempt ID.** Links all frames within one continuous attempt. |
| `nfl_id` | int64 / null | 58286 | Player ID → `players.csv`. For `BALL` entity, represents the player's `nfl_id` in that event. |
| `entity_type` | str | PLAYER | Entity tracked: `PLAYER` or `BALL`. |
| `time` | str | 2025-03-02T18:56:38.200 | ISO 8601 timestamp (sampled every **0.10s**). |
| `drill_type` | str | SKILL_DRILLS_OL | Broad drill category. |
| `drill_name` | str | OL_PULL_DRILL_FOLD... | Specific drill name. |
| `attempt` | int64 | 4 | Attempt number for the prospect within the drill. |
| `x` | float64 | 87.09 | Horizontal position along field length (**yards**, 0–120). |
| `y` | float64 | 22.52 | Vertical position across field width (**yards**, 0–53.33). |
| `s` | float64 | 0.28 | Instantaneous speed (**yd/s**). |
| `a` | float64 | 0.11 | Instantaneous acceleration (**yd/s²**). |
| `dis` | float64 | 0.01 | Distance from previous frame (**yards**). |
| `dir` | float64 | 126.08 | Motion direction angle (**degrees**, 0–360). |

### `drill_type` Values

| Value | Category |
|-------|----------|
| `FORTY_YARD_DASH` | Sprint |
| `THREE_CONE_DRILL` | Agility |
| `SHORT_SHUTTLE` | Agility |
| `SKILL_DRILLS_WR` | Position-specific |
| `SKILL_DRILLS_DB` | Position-specific |
| `SKILL_DRILLS_OL` | Position-specific |
| `SKILL_DRILLS_DL` | Position-specific |
| `SKILL_DRILLS_TE` | Position-specific |

### Example `drill_name` Values

- `GAUNTLET_DRILL`
- `RUN_THE_HOOP_DRILL`
- `BACK_PEDAL_AND_TRANSITION_45_DEGREE_REACTION`
- `SLOT_STRIKE_ROUTE_LEFT`
- `PASS_PRO_MIRROR_DRILL`
- `OL_PULL_DRILL_FOLD...`
