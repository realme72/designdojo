# Uneven greens

The east–west road is busier. `set_green(direction, seconds)` sets that direction's green
duration (yellow and all-red stay shared). It takes effect immediately, including for a
green that is currently showing (its remaining time is recomputed from when it started).
`seconds < 1` raises `InvalidDuration`. Everything else (emergency, flashing, catching up
after long idle periods) works as before with the new cycle length.

*Interviewer's question:* how many places assumed both greens were equal?
