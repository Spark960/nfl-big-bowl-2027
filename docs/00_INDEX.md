# NFL Big Data Bowl 2027 — Knowledge Base Index

> **Purpose:** Single entry point to all competition reference material.  
> **Rule:** Never re-read the Kaggle website. Everything is captured here.

---

## 📁 Documentation Map

| File | Contents | When to Read |
|------|----------|--------------|
| [`01_competition_overview.md`](./01_competition_overview.md) | Theme, goal, timeline, submission rules, judging criteria | Starting a new analysis direction or writing up |
| [`02_data_catalog.md`](./02_data_catalog.md) | File inventory, sizes, row counts, ERD diagram | Deciding which files to load |
| [`03_data_dictionary_combine.md`](./03_data_dictionary_combine.md) | Column definitions for `players.csv`, `combine_results.csv`, `combine_tracking.csv` | Working with Combine-side data |
| [`04_data_dictionary_nfl.md`](./04_data_dictionary_nfl.md) | Column definitions for `games.csv`, `player_play.csv`, `game_tracking_*.csv`, `player_career_successes.csv` | Working with NFL-side data |
| [`05_ideas_and_strategy.md`](./05_ideas_and_strategy.md) | Example research directions, creative ideas, evaluation rubric | Brainstorming or scoping work |
| [`06_field_coordinate_system.md`](./06_field_coordinate_system.md) | Coordinate system diagram and conventions for tracking data | Interpreting x/y/dir/o columns |
| [`07_winning_game_plan.md`](./07_winning_game_plan.md) | **🏆 Final strategy**: 3 proposals, 3 teardowns, winning proposal with full methodology | The battle plan |
| [`08_execution_plan.md`](./08_execution_plan.md) | **🎯 Execution plan**: 7 phases, granular checklists, data refs, exit criteria | What to do next |
| [`09_phase1_eda_summary.md`](./09_phase1_eda_summary.md) | **📊 Phase 1 EDA summary**: DL cohort, drill catalog, 10 Hz signal quality, NFL snap thresholds | Reference for Phase 2–4 |

---

## 📂 Data Location

```
data/nfl-big-data-bowl-2027/
├── players.csv                  (47 KiB  · 510 rows)
├── combine_results.csv          (41 KiB  · 510 rows)
├── combine_tracking.csv         (79.9 MiB · 463K rows)
├── player_career_successes.csv  (14 KiB  · 510 rows)
├── player_play.csv              (139.3 MiB · 316K rows)
├── games.csv                    (43 KiB  · 1,002 rows)
├── game_tracking_2023.csv       (319.9 MiB · 1.4M rows)
├── game_tracking_2024.csv       (684.7 MiB · 3.0M rows)
└── game_tracking_2025.csv       (975.2 MiB · 4.3M rows)
```

**Total:** ~2.2 GiB across 9 files, covering **510 rookie prospects** (draft years 2023–2025).

---

## 🔑 Key Entities & Join Keys

| Entity | Primary Key | Lives In |
|--------|-------------|----------|
| Player | `nfl_id` | `players.csv` (master) → all other files |
| Combine Drill Attempt | `event_id` + `nfl_id` + `time` | `combine_tracking.csv` |
| Game | `game_id` | `games.csv` → `player_play.csv`, `game_tracking_*.csv` |
| Play | `game_id` + `play_id` | `player_play.csv` → `game_tracking_*.csv` |
| Player-Play | `game_id` + `play_id` + `nfl_id` | `player_play.csv` |

---

## 🧠 Quick Reminders

- **Tracking data is 10 Hz** (one frame every 0.10 seconds) for both Combine and in-game.
- **Submission limit:** ≤ 2,000 words, < 10 tables/figures.
- **Must use player tracking data** — writeups that don't will not be scored.
- **Deadline:** January 6, 2027 (11:59 PM UTC).
- **Focus narrow:** Pick one position group, one drill, or one specific movement trait. Don't try to cover everything.
