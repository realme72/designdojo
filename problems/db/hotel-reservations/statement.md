# Hotel Reservations

> **Interview questions** (tab next to Problem): start there, like a real interview. Should this be
> relational or NoSQL, and why? How do you stop races? What would you index? Answer in your own words and
> get graded on the reasoning, then design the schema.

Design the reservations database for a hotel, then the operations and reports on top of it
(**PostgreSQL 17**). The key rule, no double bookings, must hold **even when two requests
race**, so it has to be enforced by the database itself.

## Requirements

1. **Room types** (e.g. Deluxe) have a unique name and a nightly rate.
2. **Rooms** have a unique number (text, e.g. `"101"`) and a room type.
3. **Guests** have a name and a unique email.
4. A **booking** is one room for one guest from `check_in` (inclusive) to `check_out`
   (exclusive): staying 1 Mar to 3 Mar is two nights. `check_out` must be after `check_in`.
5. Bookings are `CONFIRMED` or `CANCELLED`. Two **confirmed** bookings of the same room must
   never overlap. Back-to-back is fine (one checks out on the day the next checks in);
   cancelled bookings block nothing.
6. A booking's price is fixed when it is made: nights × the room type's rate **at that time**.

## Operations

| Operation | Returns |
|---|---|
| `add_room_type(:name, :nightly_rate)` | one row: `id` |
| `set_rate(:room_type_id, :nightly_rate)` | nothing |
| `add_room(:number, :room_type_id)` | one row: `id` |
| `add_guest(:email, :name)` | one row: `id` |
| `book(:room_id, :guest_id, :check_in, :check_out)` | one row: `booking_id`, `total` |
| `cancel(:booking_id)` | nothing |
| `available_rooms(:room_type_id, :check_in, :check_out)` | rows `number`: rooms of that type free for the whole stay, by number |
| `occupancy(:day)` | rows `room_type`, `occupied`, `rooms`: for every room type, rooms occupied on the night of `day`, and how many rooms it has; by room type name |
| `guest_stays(:guest_id)` | rows `number`, `check_in`, `nights`, `total`, `status`, by `check_in` |

Rejected bookings (overlap, bad dates, unknown room or guest) must change nothing.

*Hint:* Postgres has range types (`daterange`) and exclusion constraints. A trigger also works,
but think about what happens when two bookings for the same room arrive at the same time.
