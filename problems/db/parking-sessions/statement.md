# Parking Lot Sessions

> **Interview questions** (tab next to Problem): start there.

Design the database behind parking lots with entry/exit gates (**PostgreSQL 17**).

## Requirements

1. A **lot** has numbered **spots** of a type: `COMPACT`, `LARGE` or `EV`.
2. A **vehicle** is identified by its plate (unique). A **session** records a vehicle in a spot
   from entry to exit. A spot holds at most **one open session**, and a vehicle is in at most
   **one open session** anywhere.
3. On entry the vehicle gets the **lowest-numbered free spot** of its type in that lot (rejected
   if none). Unknown plates are registered on first entry.
4. **Fees** per started hour (minimum one hour): COMPACT 20, LARGE 40, EV 30. Rates may change
   later; a session keeps the fee charged at exit.

## Operations

| Operation | Returns |
|---|---|
| `add_lot(:name)` | one row: `id` |
| `add_spots(:lot_id, :type, :count)` | nothing: numbered after the lot's existing spots |
| `enter(:lot_id, :plate, :type, :at)` | one row: `spot_no` |
| `exit(:plate, :at)` | one row: `fee` |
| `occupancy(:lot_id)` | rows `type`, `occupied`, `total`: every type the lot has, by type |
| `revenue(:lot_id, :day)` | a single value: fees of sessions that exited that UTC day |
