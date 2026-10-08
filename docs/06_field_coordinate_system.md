# Field Coordinate System

## Diagram

![NFL Field Coordinate System](./images/field_coordinate_system.png)

---

## Coordinate Conventions

| Dimension | Range | Description |
|-----------|-------|-------------|
| **x** | 0 – 120 yards | Horizontal position along field length (includes both end zones, each 10 yards). |
| **y** | 0 – 53.33 yards | Vertical position across field width. |

### Orientation

- **x = 0**: Home end zone (left side)
- **x = 120**: Visitor end zone (right side)
- **y = 0**: Home sideline (bottom)
- **y = 53.33**: Visitor sideline (top)

### Direction & Orientation Angles

| Property | Column | Description |
|----------|--------|-------------|
| Motion direction | `dir` | Direction the player is **moving** (0–360°) |
| Body orientation | `o` | Direction the player's **body is facing** (0–360°) — *game tracking only* |

- **0°** = toward the **visitor end zone** (right / positive x)
- Angles increase **clockwise**
- **90°** = toward the **home sideline** (bottom / decreasing y)
- **180°** = toward the **home end zone** (left / negative x)
- **270°** = toward the **visitor sideline** (top / increasing y)

> [!IMPORTANT]
> `o` (body orientation) is only available in **game tracking** data, not in Combine tracking data. The difference between `o` and `dir` reveals whether a player is running sideways, backpedaling, etc.

---

## Column Availability by Data Source

| Column | `combine_tracking.csv` | `game_tracking_*.csv` |
|--------|:---------------------:|:---------------------:|
| `x` | ✅ | ✅ |
| `y` | ✅ | ✅ |
| `s` (speed) | ✅ | ✅ |
| `a` (acceleration) | ✅ | ✅ |
| `dis` (distance) | ✅ | ✅ |
| `dir` (direction) | ✅ | ✅ |
| `o` (orientation) | ❌ | ✅ |
| `event` | ❌ | ✅ |
| `entity_type` | ✅ | ❌ |
| `event_id` | ✅ | ❌ |
| `drill_type` | ✅ | ❌ |
| `drill_name` | ✅ | ❌ |
| `attempt` | ✅ | ❌ |
