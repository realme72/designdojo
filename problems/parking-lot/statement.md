# Parking Lot

Design and implement the core of a multi-floor parking lot.

## Requirements

1. The lot has one or more **floors**, numbered from 1. Each floor has some number
   of `SMALL`, `MEDIUM` and `LARGE` spots.
2. Vehicle ↔ spot compatibility:
   - `BIKE` fits any spot
   - `CAR` fits `MEDIUM` or `LARGE`
   - `TRUCK` fits `LARGE` only
3. **Allocation rule**: a vehicle gets the *smallest compatible size* that has a free
   spot. Among spots of that size, pick the *lowest floor*. (A car takes a MEDIUM on
   floor 3 before a LARGE on floor 1.)
4. `park(plate, vehicle_type)` issues a `Ticket` stamped with `clock.now()`.
   - No compatible free spot → `LotFull`
   - That plate is already parked → `AlreadyParked`
5. `unpark(ticket_id)` frees the spot and returns a `Receipt`.
   - Fee = hours × hourly rate of the **spot's size** (not the vehicle's type).
   - Hours = duration rounded **up** to the next whole hour, minimum 1 hour.
     (0 s → 1 h, 3600 s → 1 h, 3601 s → 2 h.)
   - Unknown or already-used ticket → `InvalidTicket`
6. `available(size)` returns the number of free spots of that size across all floors.
7. The lot is used by many gates at once: **every operation must be thread-safe**.
   Two cars must never get the same spot, and a ticket can be redeemed only once.

## The contract

The judge calls only the API in `contract/` (generated; don't edit it). Your system is
built by `Solution.create(config, clock)` (Java) / `solution.create(config, clock)`
(Python). Everything behind that is your design.

Use the injected `Clock` for all time. Tests control it.

## Things an interviewer will push on

- How would you add a new vehicle type, a new spot type, or a new pricing rule?
- Where does the allocation policy live, and could you swap it?
- What exactly is locked, and for how long?
