# Recurring meetings

Standups repeat. `book_recurring(organizer, attendees, start, end, every_seconds, count)` books
`count` occurrences (`start + k × every_seconds`, k = 0..count-1) **in the same room**, chosen by
the usual policy among rooms free for *every* occurrence. All or nothing: if no single room can
host all of them, raise `NoRoomAvailable` and book nothing. `count < 1`, `every_seconds` shorter
than the meeting, or a bad first interval → `InvalidInterval`. Returns the bookings in time order.

*Interviewer's question:* is a series one booking or many, and what does cancel mean for it?
