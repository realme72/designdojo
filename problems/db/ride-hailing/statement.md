# Ride Hailing (Uber)

> **Interview questions** (tab next to Problem): start there.

Design trips and dispatch for a ride-hailing app (**PostgreSQL 17**).

## Requirements

1. **Riders** have a name. **Drivers** have a name, a vehicle class (`MINI`, `SEDAN`, `SUV`),
   an online flag and a last known location (lat, lng).
2. A **trip** has a rider, a class, a pickup point and a request time. When requested it is
   assigned to the **nearest** online driver of that class who isn't on a trip (straight-line
   distance on lat/lng degrees is fine; ties by driver id); if none, the request is rejected.
3. A driver has at most **one active trip** (`ACCEPTED`); so does a rider.
4. **Completing** a trip records the distance and the fare: base + per-km by class —
   MINI 50 + 10/km, SEDAN 80 + 14/km, SUV 120 + 20/km. Trips can be `CANCELLED` while accepted.

## Operations

| Operation | Returns |
|---|---|
| `add_rider(:name)`, `add_driver(:name, :class)` | one row: `id` |
| `driver_status(:driver_id, :online, :lat, :lng)` | nothing |
| `request(:rider_id, :class, :lat, :lng, :at)` | one row: `trip_id`, `driver` |
| `complete(:trip_id, :km)` | one row: `fare` |
| `cancel(:trip_id)` | nothing |
| `earnings(:from, :to)` | rows `driver`, `trips`, `earned`: completed trips requested in `[from, to)`, every driver (0s included), by earned desc then name |
