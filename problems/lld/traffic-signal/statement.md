# Traffic Signal Controller

Design the controller for a 4-way intersection with two directions, `NS` and `EW`.
Everything is driven by the injected clock; there are no timers.

## Requirements

1. Phases cycle in order, each lasting its configured duration:
   `NS_GREEN (green) → NS_YELLOW (yellow) → ALL_RED_TO_EW (all_red) → EW_GREEN (green) →
   EW_YELLOW (yellow) → ALL_RED_TO_NS (all_red) → NS_GREEN …`. The controller starts in
   `NS_GREEN` at creation time.
2. `phase()` returns the current phase and `remaining()` the seconds left in it.
   A phase that started at `t` with duration `d` ends at `t + d` (the next phase begins then).
3. `light(direction)` → `GREEN`, `YELLOW` or `RED` for that direction (in `ALL_RED_*` both are red).
4. `emergency(direction)`: an emergency vehicle needs `direction` green.
   - Its green phase is current → that green phase restarts (full duration from now).
   - The other direction's green phase is current → it ends now (its yellow starts now).
   - A transition (yellow / all-red) is in progress → nothing changes.
5. `set_mode(FLASHING)`: every light shows `YELLOW` and `phase()` is `FLASHING` until
   `set_mode(NORMAL)`, which restarts the cycle at `NS_GREEN` from now. Emergencies are
   ignored while flashing.

## Things an interviewer will push on

- Phases as a State machine: where do durations and transitions live?
- How would you add a pedestrian phase or a left-turn arrow?
- Why compute state from the clock instead of running a timer thread?
