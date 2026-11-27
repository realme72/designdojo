# Meeting Room Scheduler

Design meeting-room booking for an office. Times are epoch seconds; a booking occupies
the half-open interval `[start, end)`.

## Requirements

1. `add_room(room_id, capacity)`; repeated id → `DuplicateRoom`; `capacity < 1` → `InvalidCapacity`.
2. `book(organizer, attendees, start, end)` picks a room automatically: among rooms with
   `capacity ≥ attendees` that are free for the whole interval, the one with the **smallest
   capacity** (ties → lowest room id). Returns `{id, room, organizer, start, end}`.
   `end ≤ start` or `start` before now → `InvalidInterval`; nothing fits → `NoRoomAvailable`.
3. Back-to-back meetings are fine (`[9,10)` and `[10,11)` don't overlap).
4. `cancel(booking_id)` frees the room (`UnknownBooking` if unknown or already cancelled).
5. `bookings(room_id)` lists a room's bookings sorted by start. `free_slots(room_id, start, end)`
   lists the free gaps within `[start, end)` as `{start, end}`, sorted, omitting empty gaps.
   Unknown room → `UnknownRoom`; `end ≤ start` → `InvalidInterval`.
6. People book at the same time from many laptops: a room is never double-booked.

## Things an interviewer will push on

- How do you check overlap quickly with thousands of bookings per room (interval tree, sorted list)?
- Where does the room-selection policy live? What if you wanted "nearest to the organizer"?
- Recurring meetings: how would you model them?
