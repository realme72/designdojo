# Music Streaming (Spotify)

> **Interview questions** (tab next to Problem): start there.

Design the catalog, playlists and listening history of a music service (**PostgreSQL 17**).

## Requirements

1. **Artists** (unique name). **Tracks** have a title, a duration in seconds (> 0) and **one or
   more artists** (features are common); the first-listed artist is the primary one.
2. **Playlists** belong to a user (users have a name) and hold tracks in a **user-chosen order**.
   A track may appear in a playlist more than once.
3. Every **play** is recorded: who, which track, when, and how many seconds were listened
   (0 to the track's duration).

## Operations

| Operation | Returns |
|---|---|
| `add_artist(:name)`, `add_user(:name)` | one row: `id` |
| `add_track(:title, :duration_s, :artist_ids)` | one row: `id` (`:artist_ids` in credit order; at least one) |
| `create_playlist(:user_id, :name)` | one row: `id` |
| `append(:playlist_id, :track_id)` | nothing: adds at the end |
| `move(:playlist_id, :from_pos, :to_pos)` | nothing: moves the entry at position `from_pos` (1-based) to `to_pos`, shifting the others |
| `play(:user_id, :track_id, :played_at, :seconds)` | nothing |
| `playlist(:playlist_id)` | rows `position`, `title`, `artists` (comma+space separated, credit order) |
| `top_tracks(:artist_id, :n)` | rows `title`, `plays`: the artist's tracks by plays that lasted ≥ 30 s, ties by title |
| `listening_minutes(:user_id, :day)` | a single value: whole minutes listened that UTC day (rounded down) |
