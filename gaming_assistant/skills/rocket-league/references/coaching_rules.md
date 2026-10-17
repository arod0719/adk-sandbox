# Rocket League Coaching & Statistical Evaluation Rules

## Core Ratio Benchmarks
When analyzing a player's career and season metrics, apply the following diagnostic benchmarks:

### 1. Shot Accuracy Percentage (`goals / shots * 100`)
- **< 40.0% (Under-converting):** The player takes low-percentage shots from difficult angles or lacks striking power. Recommend custom training packs for power shots and aiming at high corners.
- **40.0% - 47.9% (Consistent):** Solid mechanics and good shot selection.
- **≥ 48.0% (Clinical Finisher):** Extremely selective and lethal in front of the net. Recommend focusing on playmaking and defensive positioning rather than shooting mechanics.

### 2. Defensive Ratios (`saves / wins`)
- **> 1.8 Saves per Win (Defensive Overload):** The player is spending too much time trapped in their defensive third, likely due to hesitant rotations or double-committing teammates. Advise faster challenges and shadow defense.
- **0.9 - 1.5 Saves per Win (Balanced):** Healthy defensive contribution and fluid rotational flow.
- **< 0.8 Saves per Win (Aggressive Rotator):** Highly offensive playstyle. Ensure they are not leaving open backposts or getting caught out of position.

### 3. Playmaking Ratios (`assists / wins`)
- **≥ 0.8 Assists per Win (Master Playmaker):** Excellent team chemistry and backboard centering ability.
- **< 0.4 Assists per Win (Solo Focus):** Tends to play solo or finish plays independently. Encourage infield passing and backboard back-passes.

## Training Pack Search Strategy
When coaching advice is requested:
1. Identify the player's primary rank (e.g. Grand Champion I, Diamond III) and gamemode (2v2, 3v3, 1v1).
2. Match their lowest ratio (e.g. low shot accuracy or high defensive overload) with a specific training focus.
3. Call `google_search_agent` to retrieve active custom training pack codes (e.g. `"Rocket League Grand Champion shooting training pack codes"`) and link top YouTube guide videos.
