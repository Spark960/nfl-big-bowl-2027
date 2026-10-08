# 🏆 NFL Big Data Bowl 2027 — Winning Game Plan

## Executive Summary

This document develops a winning competition strategy through **3 candidate proposals**, each subjected to a **brutal constructive teardown**, converging on a **final battle-tested proposal** designed to win.

---

## The Judging Lens (What Actually Wins)

Before proposing anything, let's internalize what judges — **NFL team analytics staff** — actually care about:

| Priority | What They Ask | Implication |
|----------|--------------|-------------|
| 🥇 **Novelty** | "Have I seen this before?" | Must go beyond "fast players are fast in games" |
| 🥈 **Actionability** | "Can our scouts use this Monday morning?" | Must produce a clear, intuitive metric or framework |
| 🥉 **Rigor** | "Is the methodology sound?" | Need statistical evidence, not just vibes |
| 4 | **Accessibility** | "Can a non-data-scientist GM understand this?" | Clear visuals, compelling narrative |
| 5 | **Tracking data value-add** | "Why do we need sensors when we have a stopwatch?" | Must show tracking reveals what times cannot |

> [!IMPORTANT]
> The #1 differentiator in past BDB winners: **laser focus on one specific insight, executed beautifully**, not a broad survey of many weak findings.

---

## Data Reality Check (Grounding the Proposals)

Before strategy, here's what we're actually working with:

### Position Group Sample Sizes
| Group | Count | Combine Drill Attempts | Key NFL Metric Availability |
|-------|-------|----------------------|----------------------------|
| **WR** | 106 | 1,529 (SKILL_DRILLS_WR) | `separation_at_pass_forward` 88%, `route_ran` 100%, `cushion` 95% |
| **OL (T+G+C)** | 121 | 910 (SKILL_DRILLS_OL) | `pressure_allowed` 57%, `sack_allowed` 57%, `peak_pressure_prob` 55% |
| **DB (CB+SS+FS)** | 118 | 1,170 (SKILL_DRILLS_DB) | `coverage_assignment` 50%, `tackle` 9% |
| **Edge (DE+OLB)** | 66 | 1,007 (SKILL_DRILLS_DL) | `player_get_off` 67%, `sack` 56%, `time_to_pressure` 6% |
| **DT+NT** | 52 | shares DL drills | Same as Edge but fewer players |
| **TE** | 42 | 438 (SKILL_DRILLS_TE) | Mixed OL/WR metrics |

### Available Combine Drills (by richness)
| Drill | Frames | Players | What It Tests |
|-------|--------|---------|---------------|
| SKILL_DRILLS_WR | 120K | 107 | Route running, catching |
| SKILL_DRILLS_DB | 95K | 122 | Backpedal, transitions, reaction |
| SKILL_DRILLS_DL | 77K | 114 | Pass rush moves, agility |
| SKILL_DRILLS_OL | 61K | 121 | Pass protection, pulling |
| FORTY_YARD_DASH | 42K | 418 | Straight-line speed (all positions) |
| SKILL_DRILLS_TE | 37K | 42 | Hybrid route/blocking |
| THREE_CONE_DRILL | 16K | 160 | Agility (multi-position) |
| SHORT_SHUTTLE | 12K | 170 | Lateral agility (multi-position) |

---

# PROPOSAL 1: "Route-Breaking Quality Score" — WR Separation from Combine to Sundays

## The Pitch

Create a **"Break Quality Score" (BQS)** from WR Combine skill drill tracking that measures how efficiently a receiver decelerates into route breaks and re-accelerates out of cuts. Show it predicts in-game separation better than the 3-cone or shuttle time.

### Combine Metrics (from `SKILL_DRILLS_WR` tracking)
Drills like `COMEBACK_ROUTE_RIGHT`, `SLANT_ROUTE_LEFT`, `POST_CORNER_ROUTE_RIGHT`, `CURL_ROUTE_RIGHT` — all have distinct break points.

- **Deceleration rate** entering the cut (slope of `s` decline)
- **Speed floor** at the break point (minimum `s` during the cut)
- **Re-acceleration burst** coming out (slope of `s` increase after the break)
- **Direction change sharpness** (rate of `dir` change, degrees/second)
- **Speed retention ratio** = speed_at_break / speed_before_deceleration

### NFL Validation
- `separation_at_pass_forward` on matching route types (88% available!)
- `yards_after_catch` vs `expected_yards_after_catch` (YAC over expected)
- Group by `route_ran` to compare Combine route-specific breaks to game route-specific outcomes

### Why It Could Win
- ✅ 106 WRs — largest skill position group
- ✅ 1,529 drill attempts with rich route data (COMEBACK, SLANT, POST_CORNER, CURL, etc.)
- ✅ `separation_at_pass_forward` is 88% available — excellent validation metric
- ✅ Route-specific drill-to-game mapping is clean
- ✅ Visually compelling: overlay Combine route path vs. game route path

---

## 🔨 TEARDOWN 1: Why This Probably Loses

### Problem 1: Competition Saturation 🚨
WR route analysis is the **single most obvious direction** in this competition. With 106 WRs and the most intuitive Combine-to-NFL story, **30-50% of submissions will likely target WR routes**. Judges will be fatigued by the 15th "separation score" they read. Novelty score: **low**.

### Problem 2: Confounders Everywhere
In-game separation depends on far more than the WR's break quality:
- **QB timing** — a late throw kills separation regardless of the break
- **Defensive scheme** — zone vs. man changes separation mechanics entirely
- **Route concept** — a WR running a clear-out route deliberately has low separation
- **Play design** — RPOs, screens, and motions affect alignment

We'd need to control for `team_coverage_man_zone`, `team_coverage_type`, `cushion`, `offense_formation`, `receiver_alignment`. This is a **regression with many controls** on a dataset of ~106 WRs — thin.

### Problem 3: Combine Drills ≠ Game Routes
Combine routes are run **against air** (no defender), at **full effort**, on a **clean field**. Game routes have:
- Press coverage requiring release moves
- Underneath defenders forcing route adjustments
- Read-option routes that change based on coverage
- Fatigue and game-speed decision-making

The drill-to-game "translation gap" is wide for WRs. A player with perfect drill breaks might struggle against physical press coverage.

### Problem 4: Metric Discovery Is Hard
"Break quality" is intuitive in concept but hard to operationalize cleanly from 10 Hz data. At 10 frames/second, a sharp break happens over 2-3 frames (0.2-0.3 seconds). Identifying the exact "break frame" algorithmically is noisy. We'd spend significant effort on signal processing that may not yield clean results.

### Verdict: ❌ High competition, moderate rigor risk, confounder-heavy. Not the winning path.

---

# PROPOSAL 2: "The Invisible Lineman" — OL Mirror Drill Mechanics → Pass Protection

## The Pitch

Offensive linemen are the **most expensive, most frequently busted** position group in the draft (after QB). They're also the hardest to evaluate because traditional Combine metrics (40, 3-cone) barely map to their job. The `SKILL_DRILLS_OL` tracking data — especially `PASS_PRO_MIRROR_DRILL` (10,421 frames) and `FIVE_YARD_WAVE_DRILL_SLIDE_AND_SHUFFLE` (18,087 frames) — directly test lateral movement and pass protection footwork.

### Combine Metrics (from `SKILL_DRILLS_OL` tracking)
- **Lateral speed** — average and peak speed in the y-axis direction during mirror/wave drills
- **Slide-and-redirect efficiency** — how quickly they reverse lateral direction (frames from peak y-velocity in one direction to peak in the other)
- **Base maintenance** — standard deviation of `s` during sustained lateral movement (steadier = better base)
- **Recovery burst** — acceleration after being beaten laterally (can they recover?)
- **Anchor stability** — deceleration capability when absorbing a forward rush

### NFL Validation
- `pressure_allowed` rate per pass-blocking snap (57% available)
- `sack_allowed` rate
- `peak_pressure_probability_allowed` (55% available — this is gold)
- `pass_rushers_encountered` as a difficulty adjustment
- `career_games_started` / total snap share as an outcome

### Why It Could Win
- ✅ **121 OL** — largest position group in the dataset!
- ✅ **910 drill attempts** with OL-specific drills
- ✅ Highest draft bust rate → highest value-add for teams
- ✅ **Less competitive** — fewer participants will choose OL (it's "boring")
- ✅ `peak_pressure_probability_allowed` is a **continuous metric** with 55% availability — perfect for regression
- ✅ Direct drill-to-game parallel: mirror drill = pass protection
- ✅ Teams spend **top-10 picks** on OL; better evaluation here saves millions

---

## 🔨 TEARDOWN 2: Why This Has Serious Risks

### Problem 1: Isolation Problem
Pass protection is a **team skill**, not an individual one. An OL allows pressure because:
- The pass rusher was elite (rushing against Myles Garrett ≠ a practice squad DE)
- The protection scheme assigned a bad matchup
- The QB held the ball too long (`dropback_duration` > 4s)
- A stunt/twist confused the assignment
- The center made the wrong protection call

We **cannot see the opposing pass rusher's tracking data** (only the 510 rookies are tracked). We can't control for opposition quality. This is a MASSIVE confounder.

### Problem 2: Drills Against Air
The mirror drill is performed against a **coach or cone**, not a real pass rusher. There's no:
- Hand fighting
- Power/bull rush to anchor against
- Counter moves
- Stunt recognition

The movement pattern in a mirror drill is fundamentally different from game pass protection. A player might have elite lateral agility in a drill but terrible hand placement or anchor strength, both unobservable in tracking data.

### Problem 3: Metric Density Problem
Unlike WRs (who have `separation_at_pass_forward` on every targeted play), OL metrics only fire on **pass plays**, and `time_to_pressure_allowed` is only available when pressure actually occurs (4.6% of plays). The signal is sparse.

### Problem 4: "Boring" Can Cut Both Ways
While fewer competitors means less saturation, OL analysis also carries a **presentation risk**. It's harder to create the "wow" visual that makes judges remember your submission. No flashy route animations, no highlight-reel plays.

### Verdict: ⚠️ Highest ceiling if isolation problems can be mitigated, but significant methodological risk. The confounders could undermine the whole analysis.

---

# PROPOSAL 3: "Burst and Bend" — Edge Rusher Explosion Profiles → Pass Rush Dominance

## The Pitch

Edge rushers (DE + OLB) are the **2nd most valuable position** in football. Teams routinely spend top-3 picks on them. The difference between an All-Pro edge rusher and a bust is often described as **"bend"** — the ability to corner the edge at speed — and **"get-off"** — the explosive first step. Both are observable in tracking data but invisible to a stopwatch.

### Combine Metrics (from `SKILL_DRILLS_DL` + `THREE_CONE_DRILL` + `FORTY_YARD_DASH`)
- **First-Step Explosion Index** — peak `a` in frames 1-5 (first 0.5s) of DL drills and 40-yard dash
- **Cornering Speed Retention** — in 3-cone and DL drills, when `dir` changes > 45°, what % of `s` is maintained? (`s_at_turn / s_before_turn`)
- **Transition Fluidity** — time (frames) to complete a direction change while maintaining speed
- **Acceleration Curve Shape** — from 40-yard dash: is the curve front-loaded (explosive start) or back-loaded (top-end speed)?
- **Bend Proxy** — in `PASS_RUSH_DRILL` / `PASS_RUSH_DROP`, the curvature of the x-y path (tighter radius = better bend)

### NFL Validation
- `player_get_off` — 67% available — **direct parallel** to First-Step Explosion
- `sack` rate per rushing snap (56% available)
- `time_to_pressure` (only 6% — but represents the plays where pressure occurs)
- `quick_pressure` (pressure within 2.5s)
- `career_games_started` and All-Pro/Pro Bowl as outcomes
- Game tracking rush paths for visual comparison

### Why It Could Win
- ✅ Edge rushers are the **highest-value non-QB position** — every team cares
- ✅ `player_get_off` is a **direct Combine-to-NFL parallel** (first-step at Combine → first-step in game)
- ✅ "Bend" is the most talked-about but **never quantified** trait — true novelty
- ✅ 114 DL skill drill participants with 1,007 attempts — reasonable sample
- ✅ **Visually spectacular** — can animate rush paths comparing Combine drill arcs to game rush arcs
- ✅ Case study potential: "Player X's tracking showed elite bend at the Combine. He was drafted in round 3. He's now leading the league in pressures."
- ✅ Multiple drills to extract from: `PASS_RUSH_DRILL`, `PASS_RUSH_DROP`, `RUN_AND_CLUB_DRILL`, plus general agility drills

---

## 🔨 TEARDOWN 3: The Honest Problems

### Problem 1: Sample Size Tension
66 edge rushers across 3 draft classes. After splitting by draft year and controlling for confounders, statistical power drops fast. A regression with 66 observations and 4-5 predictors is fragile. One outlier (say, Will Anderson or Jalen Carter) could swing the whole result.

**Mitigation:** Expand to all 114 SKILL_DRILLS_DL participants (includes DTs). Interior pass rushers also use get-off and bend. Frame it as "pass rusher" rather than just "edge."

### Problem 2: "Bend" Isn't Truly New in Concept
NFL scouts have talked about "bend" for decades. The judges — NFL analytics staff — already know bend matters. Saying "we quantified bend from tracking data" is incremental, not revolutionary. We need to show something BEYOND just "bend predicts success."

**Mitigation:** The novel angle isn't "bend matters" — it's **"here's what the stopwatch MISSES."** Show two players with identical 3-cone times but different cornering speed retention scores, and show the tracking-derived metric predicts NFL success while the 3-cone time doesn't differentiate them. The story is about **tracking data value-add over traditional metrics**, not about bend per se.

### Problem 3: `time_to_pressure` Sparsity
The best NFL outcome metric (`time_to_pressure`) is only available on 6% of plays. `sack` is binary and rare. We're mostly relying on `player_get_off` (67%), which is a process metric, not an outcome metric.

**Mitigation:** Engineer a **pressure rate** (pressures / pass rush snaps) as an aggregate player-level metric. Also use `career_games_started`, `career_defensive_snaps`, and career accolades as long-run outcome measures.

### Problem 4: DL Drills Against Air (Same Issue as OL)
Pass rush drills are against air or coaches holding pads. Real pass rushing involves:
- Hand fighting with a 320-lb tackle
- Reacting to the OL's set point
- Counter moves mid-rush
- Stunts and games

**Mitigation:** This is inherent to ALL Combine-to-NFL analyses — the entire competition is about this translation gap. Acknowledge it directly. The key insight is that **movement quality in a drill reveals neuromuscular capacity** even if the game context is different. An athlete who retains speed through turns against air will also retain more speed through turns against an OL.

### Verdict: ⚠️ Strong direction with fixable weaknesses. The sample size is the biggest concern, but expanding to all DL pass rushers helps. The "stopwatch comparison" angle elevates it from incremental to novel.

---

# THE SYNTHESIS — What We Learned from the Teardowns

| Dimension | Proposal 1 (WR) | Proposal 2 (OL) | Proposal 3 (Edge) |
|-----------|:---:|:---:|:---:|
| **Novelty** | 🔴 Low (saturated) | 🟢 High (nobody picks OL) | 🟡 Medium-High |
| **Sample Size** | 🟢 106 players | 🟢 121 players | 🟡 66→114 with DTs |
| **NFL Metric Quality** | 🟢 `separation` 88% | 🟡 `pressure_allowed` 57% | 🟢 `player_get_off` 67% |
| **Drill-Game Parallel** | 🟡 Routes ≠ game routes | 🟡 Mirror ≠ real blocking | 🟢 Explosion ≈ get-off |
| **Confounder Risk** | 🔴 QB timing, scheme, coverage | 🔴 Can't see opposing rusher | 🟡 Moderate |
| **Visual Appeal** | 🟢 Route animations | 🔴 Hard to make exciting | 🟢 Rush path animations |
| **Actionability** | 🟡 Many teams already study this | 🟢 Teams desperately want OL eval tools | 🟢 High-draft-capital position |
| **Value to NFL Teams** | 🟡 Medium | 🟢 Very High | 🟢 Very High |

### Key Insight from Teardowns:
> The winning submission must answer ONE question that no stopwatch can: **"What does the tracking data reveal that traditional Combine metrics miss, and does it predict NFL success?"**

Every proposal needs the **"stopwatch comparison" test**: take your tracking-derived metric, show it adds predictive power BEYOND the traditional Combine measurement, and demonstrate this with real player examples.

---

# 🏆 FINAL WINNING PROPOSAL

## "The Deceleration Advantage: What the Stopwatch Misses About How NFL Pass Rushers Move"

### Core Thesis

> Two pass rushers run identical 3-cone times. One decelerates 40% faster into direction changes, retaining speed through turns. The other brakes hard and rebuilds. The tracking data reveals this difference. The stopwatch cannot. The one who retains speed becomes an All-Pro. The other is out of the league in three years.

### Why This Specific Angle Wins

| Factor | Why It's Superior |
|--------|-------------------|
| **Novel metric** | "Deceleration efficiency" and "cornering speed retention" have never been quantified from Combine tracking data |
| **Clear stopwatch gap** | Directly compares tracking-derived metrics against traditional 3-cone/shuttle times — shows what tracking ADDS |
| **Focused** | One position group (DL pass rushers), one movement quality (deceleration/redirection), one question |
| **High value** | Pass rushers are the 2nd most expensive position; busting on an edge rusher costs \$30M+ |
| **Best data fit** | `player_get_off` (67% available) is a direct parallel; 114 DL players with 1,007 drill attempts |
| **Visually compelling** | Speed-through-turns animations, acceleration curve comparisons, case study player profiles |
| **Narrative arc** | "The Combine has always been about the stopwatch. Here's what it's been missing." |

---

### Methodology

#### Phase 1: Combine Feature Engineering

**From `combine_tracking.csv`** (SKILL_DRILLS_DL, THREE_CONE_DRILL, SHORT_SHUTTLE, FORTY_YARD_DASH):

| Metric | Computation | What It Captures |
|--------|------------|-----------------|
| **Peak Deceleration Rate (PDR)** | Maximum negative Δs/Δt during direction changes > 30° | How hard can they brake |
| **Cornering Speed Retention (CSR)** | `min(s) during turn / s before turn` averaged across all turns | How much speed they keep through direction changes |
| **Turn Recovery Time (TRT)** | Frames from min speed during turn to 90% of pre-turn speed | How fast they rebuild speed after a cut |
| **First-Step Explosion (FSE)** | Peak `a` in frames 1–5 of each drill attempt | Raw explosive starting ability |
| **Acceleration Curve Shape (ACS)** | Ratio of avg acceleration in frames 1–10 vs frames 11–20 in the 40-yard dash | Front-loaded (explosive) vs back-loaded (top-speed) runner |
| **Directional Jerk** | Smoothness of direction change (2nd derivative of `dir`) | Movement fluidity vs herky-jerky transitions |

> [!TIP]
> CSR (Cornering Speed Retention) is the **headline metric** — the single number that tells the story. The others support it.

#### Phase 2: NFL Outcome Engineering

**From `player_play.csv`** (filtered to DL pass rushing snaps):

| Metric | Computation | Meaning |
|--------|------------|---------|
| **Pressure Rate** | (plays with `time_to_pressure` not null) / (total pass rush snaps) | Core production metric |
| **Quick Pressure Rate** | sum(`quick_pressure`) / pass rush snaps | Explosiveness in games |
| **Avg Get-Off Time** | mean(`player_get_off`) | First-step speed in games |
| **Sack Rate** | sum(`sack`) / pass rush snaps | High-value outcome |
| **TFL Rate** | sum(`tackle_for_loss`) / defensive snaps | Run-defense disruption |

**From `player_career_successes.csv`:**

| Metric | Meaning |
|--------|---------|
| **Snap Share** | `career_defensive_snaps / career_games_active` | Playing time earned |
| **Start Rate** | `career_games_started / career_games_active` | Durability + trust |
| **Accolades** | All-Pro + Pro Bowl selections | Elite tier |

**From `game_tracking_*.csv`** (optional but powerful):

| Metric | Computation | Meaning |
|--------|------------|---------|
| **In-Game CSR** | Same cornering speed retention formula applied to game rush paths | Does the Combine trait translate to game movement? |
| **Rush Path Curvature** | Radius of curvature on pass rush arcs | Bend in real games |

#### Phase 3: The Analysis

```
Step 1: Compute all Combine tracking metrics for 114 DL players
Step 2: Compute all NFL outcome metrics for the same players
Step 3: Correlation matrix — which Combine tracking metrics predict which NFL outcomes?
Step 4: THE KEY TEST — Regression comparing:
        Model A: Traditional metrics only (3-cone, shuttle, 40, athleticism score)
        Model B: Traditional + tracking-derived metrics (CSR, PDR, TRT, FSE)
        → Show Model B has significantly better R² / AIC / cross-validated prediction
Step 5: Case studies — find "hidden gems" and "red flags" that tracking metrics identified
         but traditional metrics missed
Step 6: Visualizations — acceleration curves, rush path animations, metric comparison plots
```

#### Phase 4: The Narrative Arc (2,000 words)

```
Section 1 (200 words): The Problem
  "The Combine stopwatch tells you HOW FAST. Tracking data tells you HOW."

Section 2 (300 words): The Metric
  Introduce Cornering Speed Retention (CSR). Explain with a visual.
  Show two players: same 3-cone time, different CSR.

Section 3 (400 words): The Evidence
  Model comparison table. CSR predicts pressure rate beyond traditional metrics.
  Scatter plots: CSR vs pressure rate, colored by draft round.

Section 4 (400 words): The Translation
  Show that Combine CSR correlates with in-game CSR from game tracking.
  Side-by-side animations: Combine rush path vs game rush path.

Section 5 (400 words): Case Studies (2-3 players)
  "Player A: 3-cone of 7.10 (average). CSR of 0.85 (elite). Drafted 3rd round. 
   Now has 25 sacks in 2 seasons."
  "Player B: 3-cone of 6.95 (good). CSR of 0.62 (poor). Drafted 1st round. 
   Career pressure rate in bottom quartile."

Section 6 (300 words): Actionable Recommendations
  "When evaluating DL prospects, compute CSR from their tracking data.
   Prospects with CSR > 0.80 are 2.5x more likely to reach a pressure rate above league average,
   regardless of their traditional agility times."
```

---

### Visual Plan (< 10 figures)

| # | Figure | Purpose |
|---|--------|---------|
| 1 | **Acceleration curve comparison** — Two players with same 3-cone time, different profiles | Hook the reader with the core insight |
| 2 | **CSR distribution by career outcome tier** (violin plot) | Show metric separates NFL tiers |
| 3 | **Model comparison table** — Traditional vs. Traditional+Tracking R² | Statistical evidence |
| 4 | **Scatter: CSR vs. NFL Pressure Rate** (colored by draft round) | Key relationship visualization |
| 5 | **Combine drill path animation** (top CSR vs. bottom CSR player) | Visual "aha moment" for how CSR manifests |
| 6 | **Game rush path comparison** (same two players) | Show the trait carries over to games |
| 7 | **Case study player cards** (2-3 players) | Make it personal and memorable |
| 8 | **Feature importance plot** — What predicts NFL production? | Show tracking features ranking |

*(8 figures — well under the 10 limit, leaving room for 1 table)*

---

### Risk Mitigation Plan

| Risk | Mitigation |
|------|-----------|
| Sample size (66 edge, 114 all DL) | Use all DL pass rushers (114). Use bootstrapped confidence intervals. Focus on effect size, not p-values. |
| CSR might not predict outcomes | Have backup metrics (FSE, ACS). If CSR alone doesn't predict, show it adds value in combination with traditional metrics. |
| Judges find "bend" obvious | Frame as "deceleration advantage," NOT "bend." Focus on what tracking reveals that stopwatch misses. |
| Combine drills against air ≠ games | Address directly: "Drills reveal neuromuscular capacity. The question is whether capacity translates. Here's evidence it does." Then show Combine CSR → Game CSR correlation. |
| Game tracking data too large to process | Sample strategically. Only load game_tracking for identified DL pass rush plays (filter via player_play). |

---

### 12-Week Execution Timeline

| Week | Phase | Deliverable |
|------|-------|------------|
| 1–2 | **EDA & Data Wrangling** | Clean data pipelines, verify drill types, understand frame structure |
| 3–4 | **Combine Feature Engineering** | Compute CSR, PDR, TRT, FSE, ACS for all 114 DL players |
| 5–6 | **NFL Outcome Engineering** | Compute pressure rate, get-off time, sack rate per player |
| 7–8 | **Statistical Analysis** | Correlations, model comparison (Traditional vs. Traditional+Tracking) |
| 9 | **Game Tracking Validation** | Compute in-game CSR, compare to Combine CSR |
| 10 | **Case Studies & Visuals** | Build player profiles, create animations and plots |
| 11 | **Writing** | Draft the 2,000-word writeup |
| 12 | **Polish & Submit** | Review, tighten prose, finalize Kaggle notebook |

---

### Why This Wins Over the Alternatives

> [!IMPORTANT]
> **vs. WR Route Analysis (Proposal 1):** We avoid the saturated competitor pool. While 30%+ of submissions analyze WR routes, we're in a far less crowded lane with DL pass rushers. Novelty score is dramatically higher.
>
> **vs. OL Pass Protection (Proposal 2):** We share the "trench" value proposition but avoid the crippling isolation problem (can't see opposing rusher). For pass rushers, the outcome metrics (`sack`, `pressure`, `player_get_off`) are individual, not team-dependent.
>
> **vs. Generic "Bend" Analysis (Proposal 3 raw):** By framing as "Deceleration Advantage" and anchoring on the **stopwatch comparison test**, we elevate from "bend matters" (obvious) to "here's what the stopwatch misses" (novel). The CSR metric is original, intuitive, and actionable.

### The Single Sentence That Wins

> *"We quantified how NFL pass rushers retain speed through direction changes from 10 Hz Combine tracking data, showed this 'Cornering Speed Retention' metric predicts NFL pressure rates better than any traditional Combine measurement, and identified specific prospects the stopwatch would have missed."*
