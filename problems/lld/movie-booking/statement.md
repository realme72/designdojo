# Movie Ticket Booking (BookMyShow)

Design seat booking for a cinema. Picking seats places a temporary **hold**, and payment
**confirms** it into a booking. Many users race for the same seats.

## Requirements

1. `add_show(show_id, rows, cols)` creates a show with `rows × cols` seats. Seats are
   named row letter + number: rows `A, B, …`, numbers `1..cols` (e.g. `C7`).
   Duplicate id → `DuplicateShow`; `rows` outside 1–26 or `cols < 1` → `InvalidLayout`.
2. `hold(show_id, user, seats)` holds all requested seats for `hold_seconds` (from config)
   and returns a hold id. It is **all-or-nothing**: if any seat is not available, nothing is
   held and `SeatUnavailable` is raised.
   - Seat names that don't exist, an empty list, or a seat listed twice → `InvalidSeat`.
3. A hold expires when `clock.now() >= created + hold_seconds`; its seats become available.
4. `confirm(hold_id)` turns an active hold into a booking (seats sorted by row, then number
   numerically: `A2` before `A10`). An expired hold → `HoldExpired`; unknown, released or
   already-confirmed → `UnknownHold`.
5. `release(hold_id)` frees an active hold's seats (expired → `HoldExpired`, unknown → `UnknownHold`).
6. `cancel(booking_id)` frees a booking's seats; unknown or already cancelled → `UnknownBooking`.
7. `available(show_id)` counts seats that are neither actively held nor booked.
   `seat_state(show_id, seat)` is `AVAILABLE`, `HELD` or `BOOKED`.
8. Unknown show → `UnknownShow`. Use the injected `Clock` for all time.
9. Thousands of users click at once: a seat must never be held or booked twice.

## Things an interviewer will push on

- What exactly do you lock: the whole show, or individual seats? What about deadlocks?
- How would you add dynamic pricing or seat categories?
- How do holds expire without a background thread?
