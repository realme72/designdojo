# Calendar & Invites (Google Calendar)

> **Interview questions** (tab next to Problem): start there.

Design events, invitations and RSVPs (**PostgreSQL 17**).

## Requirements

1. **Users** have a name. An **event** has an organizer, a title, a start and an end (end after
   start).
2. Users are **invited** to events (at most once each). The organizer is automatically an
   attendee with response `ACCEPTED`. Others start as `INVITED` and **respond** `ACCEPTED`,
   `DECLINED` or `TENTATIVE`. Only invited users can respond.
3. Overlapping events are allowed (people double-book), but the app can report **conflicts**.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `create_event(:organizer_id, :title, :starts_at, :ends_at)` | one row: `id` |
| `invite(:event_id, :user_id)` | nothing |
| `respond(:event_id, :user_id, :response)` | nothing |
| `agenda(:user_id, :from, :to)` | rows `title`, `starts_at`, `response`: events overlapping `[from, to)` the user hasn't declined, by start then title |
| `conflicts(:user_id)` | rows `first`, `second`: pairs of overlapping events the user accepted (first starts earlier, or same start and smaller id), by first's start |
| `attendance(:event_id)` | rows `response`, `people`: per response, by response |
