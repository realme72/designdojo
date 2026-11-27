# Cinema Seat Booking (BookMyShow)

> **Interview questions** (tab next to Problem): start there.

Design seat booking for a cinema chain (**PostgreSQL 17**).

## Requirements

1. A **screen** has a name and a grid of seats: rows `A`, `B`, … and seats `1..n` per row
   (seat labels like `B7`), created with the screen.
2. A **show** plays a movie on a screen from a start to an end time. Shows on the same screen
   never overlap.
3. A **booking** reserves one or more seats of a show for a customer, all or nothing. A seat
   can be booked **once per show**, and only seats of **that show's screen** exist for it.
4. **Cancelling** a booking frees its seats.

## Operations

| Operation | Returns |
|---|---|
| `add_screen(:name, :rows, :seats_per_row)` | one row: `id` |
| `add_show(:screen_id, :movie, :starts_at, :ends_at)` | one row: `id` |
| `book(:show_id, :customer, :seats)` | one row: `booking_id` (`:seats` like `{A1,A2}`) |
| `cancel(:booking_id)` | nothing |
| `available(:show_id)` | a single value: free seats |
| `row_map(:show_id, :row)` | rows `seat`, `taken`: the row's seats in seat-number order |
| `occupancy(:movie)` | rows `starts_at`, `booked`, `capacity`: the movie's shows by start time |
