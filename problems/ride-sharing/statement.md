# Ride Sharing (Uber / Ola)

Design the dispatch core of a ride-hailing app on a simple integer grid.

## Requirements

1. Config: `max_radius` (grid units) and per vehicle class a `base_fare` and `per_unit`
   fare (cents).
2. `add_driver(driver_id, vehicle, x, y)` registers an `AVAILABLE` driver; repeated id →
   `DuplicateDriver`. `update_location(driver_id, x, y)`. `set_online(driver_id, online)`
   toggles `AVAILABLE`/`OFFLINE`; going offline (or online) while `ON_TRIP` → `InvalidState`.
3. `request_ride(rider, vehicle, x, y, dest_x, dest_y)` assigns the **nearest available
   driver of that class** by straight-line distance, within `max_radius` (inclusive).
   Ties → lowest driver id. Returns the trip with status `ASSIGNED`; the driver becomes
   `ON_TRIP`. No driver → `NoDriverAvailable`. A rider with an unfinished trip (assigned or
   started) → `RiderBusy`.
4. Trip lifecycle: `start_trip` (`ASSIGNED → STARTED`), `end_trip` (`STARTED → COMPLETED`),
   `cancel_trip` (`ASSIGNED → CANCELLED`). Anything else → `InvalidState`.
5. `end_trip` sets the fare: `base_fare + per_unit × (|dest_x − x| + |dest_y − y|)` for the
   trip's vehicle class, and the driver becomes `AVAILABLE` at the destination.
   Cancelling frees the driver where they are.
6. `trip(id)` and `driver_status(id)`; unknown → `UnknownTrip` / `UnknownDriver`.
   Fare is 0 until the trip completes.
7. Riders request concurrently: a driver must never be assigned two trips.

## Things an interviewer will push on

- How would you swap the matching strategy (rating-aware, ETA-based, batching)?
- Surge pricing: where does it plug in?
- How do you find nearby drivers fast with a million drivers (geo-indexing)?
