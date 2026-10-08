# Ideas, Strategy & Evaluation

## Example Research Directions (from competition page)

### 1. Route Running & Coverage
- Measure **change of direction, deceleration into breaks, acceleration out of cuts** for WRs and DBs
- Compare Combine drill movement traits to **in-game separation** metrics
- Link `combine_tracking` agility metrics → `separation_at_pass_forward`, `cushion`, `yards_after_catch`

### 2. Trench Play
- Evaluate **first-step quickness, lateral agility, burst** for OL/DL during agility drills
- Compare to **pass-rush or run-blocking** in-game performance
- Link `combine_tracking` → `player_get_off`, `time_to_pressure`, `pressure_allowed`, `sack_allowed`

### 3. Drill Translation
- Compare **sensor-based movement metrics** with **traditional drill times** (from `combine_results.csv`)
- Identify where tracking data adds context beyond the stopwatch number
- Example: Two players with identical 40 times but different acceleration profiles

### 4. Position-Specific Mechanics
- Analyze **body control, acceleration profiles, pursuit angles** during position drills
- Relate to **NFL rookie-season performance**
- Link `combine_tracking` drill-specific movements → `player_career_successes` outcomes

---

## Strategic Recommendations

> [!TIP]
> **Focus narrow.** The competition explicitly encourages picking **one position group, one drill, or one specific movement trait** rather than trying to evaluate every prospect across all drills.

### High-Value Angles to Consider

| Angle | Position(s) | Combine Data | NFL Data | Why It's Interesting |
|-------|-------------|-------------|----------|---------------------|
| Break quality on routes | WR, TE | `SKILL_DRILLS_WR/TE` tracking | `separation_at_pass_forward`, `route_ran` | Directly links agility to separation |
| First-step explosion | DE, DT, OLB | `SKILL_DRILLS_DL` tracking | `player_get_off`, `time_to_pressure` | Measurable in both contexts |
| Mirror ability | OL | `SKILL_DRILLS_OL` tracking | `pressure_allowed`, `sack_allowed` | Critical OL skill, poorly measured by stopwatch |
| Hip fluidity | DB | `SKILL_DRILLS_DB` tracking | `coverage_assignment`, separation allowed | Backpedal-to-transition is key DB skill |
| 40-yard dash mechanics | All | `FORTY_YARD_DASH` tracking | `s` (speed) in game tracking | Acceleration curve vs game speed usage |

### Derived Metrics to Engineer from Tracking Data

| Metric | How to Compute | Source |
|--------|---------------|--------|
| **Max acceleration** | `max(a)` per drill attempt | `combine_tracking` |
| **Deceleration rate** | Negative `a` values during direction changes | `combine_tracking` |
| **Direction change sharpness** | Rate of `dir` change over time | `combine_tracking` |
| **Speed at cut point** | `s` at frame with max `dir` change | `combine_tracking` |
| **Time to top speed** | Frames from start to `max(s)` | `combine_tracking` |
| **Lateral agility index** | `y` displacement / time during shuttle drills | `combine_tracking` |
| **Orientation-direction delta** | `abs(o - dir)` during game plays | `game_tracking_*` |

---

## Evaluation Rubric

### Pass/Fail Gates

| # | Requirement | What to Ensure |
|---|------------|----------------|
| 1 | **Combine-to-NFL Linkage** | Analysis must explicitly connect Combine tracking metrics to regular-season game performance. Not just Combine analysis alone. |
| 2 | **Writeup Completeness** | Readable markdown + embedded visuals + attached **public Kaggle Notebook**. |

### Scoring Criteria (Judges: NFL team analytics + tracking vendors)

Judges look for:
- **Novelty** — Beyond conventional scouting wisdom
- **Actionability** — Coaches and scouts can use these insights
- **Analytical rigor** — Sound statistical methodology
- **Accessibility** — Clear communication of findings

---

## Constraints Checklist

- [ ] ≤ 2,000 words
- [ ] < 10 tables/figures
- [ ] Uses player tracking data (mandatory)
- [ ] Links Combine → NFL performance (mandatory)
- [ ] Public Kaggle Notebook attached
- [ ] Code in Appendix or linked notebook (not cluttering writeup)
- [ ] Focused on specific position/drill/trait (recommended)
