# Maintenance mode

Technicians need to take an elevator out of service.

- New `set_maintenance(elevator_id, enabled)`. Turning it on clears that elevator's stops; it stays
  where it is and reports direction `MAINTENANCE`. Turning it off makes it `IDLE` at its
  current floor.
- An elevator in maintenance never moves, is never chosen for hall calls, and a car call
  (`press`) on it → `InvalidRequest`.
- If every elevator is in maintenance, a hall call → new error `NoElevatorAvailable`.

*Interviewer's question:* how many places check "is this elevator usable"?
