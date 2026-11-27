# Airline Reservation System

Design flight search, seat booking and cancellation for an airline. Times are epoch seconds.

## Requirements

1. `add_flight(flight_id, origin, destination, departs_at, seats, fares)`: `seats` and
   `fares` map each class (`ECONOMY`, `BUSINESS`) to a seat count and a base fare.
   Repeated id → `DuplicateFlight`.
2. Seats are numbered per class: `E1, E2, …` for economy, `B1, B2, …` for business.
3. `search(origin, destination, seat_class, count, start, end)` → flight ids departing in
   `[start, end)`, not yet departed, with at least `count` free seats in that class, sorted
   by departure time then id.
4. `book(passenger, flight_id, seat_class, count)` assigns the `count` **lowest-numbered**
   free seats and returns `{pnr, flight_id, seats, total}`. Checks, in order:
   `UnknownFlight`; `count < 1` → `InvalidRequest`; departed (`now ≥ departs_at`) →
   `FlightDeparted`; not enough seats → `NotEnoughSeats`.
5. **Dynamic fare**: every seat in a booking costs
   `base × (10 + floor(4 × sold / capacity)) / 10` (rounded down), where `sold` is that
   class's seats already sold before this booking (+10% per quarter of the cabin sold).
6. `cancel(pnr)` frees the seats and returns the refund: the full total if at least 24 hours
   before departure, otherwise half (rounded down). After departure, or already cancelled →
   `InvalidState`; unknown → `UnknownBooking`.
7. Many passengers book at once: seats are never sold twice and never oversold.

## Things an interviewer will push on

- Where does the fare strategy live (surge, early-bird, loyalty)?
- How would you add connecting flights in search?
- Seat holds during payment: how and for how long?
