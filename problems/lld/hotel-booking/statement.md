# Hotel Booking System

Design reservations for a single hotel. Dates are ISO strings (`YYYY-MM-DD`); "today" is
the UTC date of the injected clock.

## Requirements

1. `add_room(number, type, nightly_rate)`; repeated number → `DuplicateRoom`;
   `nightly_rate < 1` → `InvalidRate`.
2. A stay is the half-open range `[check_in, check_out)`: a room freed on a date can be
   booked from that same date. Invalid dates → `InvalidDates`: malformed, `check_out ≤
   check_in`, or `check_in` before today.
3. `search(type, check_in, check_out)` lists free room numbers of that type, sorted.
4. `book(guest, type, check_in, check_out)` reserves the **lowest-numbered** free room of
   that type (sorted as strings) and returns the reservation: `total = nights × nightly_rate`,
   status `CONFIRMED`. None free → `NoAvailability`.
5. `cancel(reservation_id)` cancels a `CONFIRMED` reservation and returns the refund:
   the full total if today is at least 2 days before check-in, otherwise half
   (rounded down). Cancelled stays free the room.
6. `check_in(id)`: only `CONFIRMED`, and only on the check-in date. `check_out(id)`: only
   `CHECKED_IN`. Wrong status or day → `InvalidState`. Unknown id → `UnknownReservation`.
7. `reservations(guest)` lists that guest's reservations (any status), sorted by check-in
   date, then by booking order.
8. Many front-ends book at once: a room must never be double-booked.

## Things an interviewer will push on

- How do you check availability efficiently for a date range?
- Where do pricing (weekend rates, seasons) and the refund policy live?
- Model the reservation lifecycle: which transitions are legal?
