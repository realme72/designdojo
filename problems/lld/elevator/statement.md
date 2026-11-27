# Elevator System

Design the controller for a bank of elevators in one building. Time is discrete: the
building calls `step()` once per tick, and each elevator moves at most one floor per tick.

## Requirements

1. Floors are numbered `1..floors`. Elevators are numbered `1..elevators`. Every elevator
   starts at floor 1, `IDLE`, with no stops.
2. **Hall call** `call(floor, direction)`: someone on `floor` wants to go `UP`/`DOWN`.
   Pick an elevator, add `floor` to its stops, and return its id.
   - `UP` from the top floor, `DOWN` from floor 1, or direction `IDLE` → `InvalidRequest`.
3. **Car call** `press(elevator_id, floor)`: someone inside presses a floor button.
4. A request for the floor an elevator is currently at, while that elevator is `IDLE`, is
   served immediately (nothing is added).
5. **Dispatch rule** for hall calls:
   - An elevator is *on the way* if it is `IDLE`, or it is moving in the requested
     direction and the floor is strictly ahead of it (`UP`: above, `DOWN`: below).
   - Among on-the-way elevators pick the nearest; if none is on the way, pick the
     nearest overall. Ties go to the lowest id.
6. **Movement** (each `step()`, elevators in id order):
   - No stops → `IDLE`, stays put.
   - `IDLE` with stops → set direction toward the nearest stop (equidistant → `UP`).
   - Move one floor. If the new floor is a stop, it is served (removed).
   - Then: no stops left → `IDLE`; no stops ahead in the current direction → reverse.
7. `status(id)` reports floor, direction, and stops in ascending order.
8. Floor outside `1..floors` → `InvalidFloor`; unknown elevator → `UnknownElevator`.
9. Hall calls arrive from many floors at once: `call` and `press` must be thread-safe.

## Things an interviewer will push on

- How would you swap the dispatch algorithm (e.g. to save energy)?
- How would you add maintenance mode or an express elevator?
- Where does "what an elevator does next" live: one big method, or its state?
