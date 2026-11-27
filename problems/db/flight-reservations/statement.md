# Flight Reservations

> **Interview questions** (tab next to Problem): start there.

Design reservations for an airline (**PostgreSQL 17**).

## Requirements

1. A **flight** has a unique code, origin and destination airports (3-letter codes, different),
   and departure/arrival times (arrival after departure).
2. A flight has numbered **seats**, each in a class: `ECONOMY` or `BUSINESS`.
3. A **reservation** has a unique PNR and a passenger name, and holds exactly one seat. A seat
   is held by at most one reservation. Booking assigns the **lowest-numbered free seat** of the
   requested class; if none is free, it is rejected.
4. **Cancelling** (by PNR) frees the seat.

## Operations

| Operation | Returns |
|---|---|
| `add_flight(:code, :origin, :destination, :departs_at, :arrives_at)` | one row: `id` |
| `add_seats(:flight_id, :class, :first_no, :last_no)` | nothing: seats `first_no..last_no` of that class |
| `book(:flight_id, :class, :passenger, :pnr)` | one row: `seat_no` |
| `cancel(:pnr)` | nothing |
| `load_factor(:flight_id)` | one row: `booked`, `capacity` |
| `connections(:origin, :destination)` | rows `first`, `second`, `layover_min`: two-flight trips via any airport where the second departs 45 minutes to 6 hours after the first arrives; by total arrival time, then codes |
